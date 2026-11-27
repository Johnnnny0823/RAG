"""Verify the paired TIPO gazette PDFs in a disposable official Compose corpus."""

import argparse
import json
import subprocess
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.parse import urlsplit

from scripts.evaluate_search import request

APPLICATION = "114106690"
BASE_URL = "https://cloud.tipo.gov.tw/S220/downloads"


@dataclass(frozen=True)
class Case:
    stage: str
    scope: str
    number: str
    issue: str
    directory: str
    pages: int
    checksum: str

    @property
    def url(self) -> str:
        return f"{BASE_URL}/{self.directory}{self.issue}/pdfdata/{APPLICATION}.pdf"


CASES = (
    Case(
        "publication",
        "fulltext",
        "202640162",
        "024019",
        "invention/pub",
        2,
        "20df47fe2d746383732d7d4878537c153919338c5735a267cf797bcce09f4dee",
    ),
    Case(
        "grant",
        "claims_only",
        "I941082",
        "053028",
        "patent/isu",
        9,
        "7b9fd5dcb190a7108770a812999e556b5126f2d0333dcf3a914ed20c91f1a615",
    ),
)


def import_pdf(
    project: str, case: Case, document_id: str
) -> subprocess.CompletedProcess:
    number_option = "--publication" if case.stage == "publication" else "--grant"
    return subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            ".env.example",
            "-p",
            project,
            "run",
            "--rm",
            "--no-deps",
            "migrate",
            "python",
            "-m",
            "services.ingestion.gazette_pdf",
            "--application",
            APPLICATION,
            number_option,
            case.number,
            "--issue",
            case.issue,
            "--expected-sha256",
            case.checksum,
            "--apply-to",
            document_id,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=90,
        check=False,
    )


def smoke(api: str, project: str) -> None:
    items = request(api, f"/patents?number_type=application&number={APPLICATION}")[
        "items"
    ]
    publication, grant = [
        next(
            item
            for item in items
            if (item["document_stage"], item["publication_no"], item["content_scope"])
            == (case.stage, case.number, case.scope)
        )["document_id"]
        for case in CASES
    ]
    rejected = import_pdf(project, CASES[1], publication)
    if (
        rejected.returncode != 1
        or "No matching official document version in this issue" not in rejected.stderr
    ):
        raise ValueError(f"Unexpected cross-version result: {rejected.stderr.strip()}")

    for case, document_id in zip(CASES, (publication, grant), strict=True):
        path = f"/patents/{document_id}"
        original = request(api, path + "/claims")
        if len(original["claims"]) != 13:
            raise ValueError(f"Unexpected claim count for {case.number}")
        for _ in range(2):
            imported = import_pdf(project, case, document_id)
            if imported.returncode:
                raise ValueError(
                    f"PDF import failed for {case.number}: {imported.stderr.strip()}"
                )
            result = json.loads(imported.stdout)
            if result != {
                "source_url": case.url,
                "sha256": case.checksum,
                "pages": case.pages,
                "attached": True,
            }:
                raise ValueError(f"TIPO PDF metadata changed for {case.number}")
        pdfs = [
            source
            for source in request(api, path)["sources"]
            if source["record_locator"] == "PDF page 1"
        ]
        if [(source["source_url"], source["artifact_sha256"]) for source in pdfs] != [
            (case.url, case.checksum)
        ]:
            raise ValueError(f"Duplicate or incorrect PDF source for {case.number}")
        if request(api, path + "/claims") != original:
            raise ValueError(f"XML claim provenance changed for {case.number}")
        extracted = request(api, f"{path}/gazette-pdfs/{case.checksum}/pages")
        if (
            extracted["artifact_sha256"] != case.checksum
            or extracted["document_id"] != document_id
            or [page["page_number"] for page in extracted["pages"]]
            != list(range(1, case.pages + 1))
            or case.number not in extracted["pages"][0]["extracted_text"]
        ):
            raise ValueError(f"Incorrect PDF page provenance for {case.number}")
        print(
            f"{case.number}: official PDF and XML claim provenance verified", flush=True
        )
    try:
        request(api, f"/patents/{publication}/gazette-pdfs/{CASES[1].checksum}/pages")
    except HTTPError as error:
        if error.code != 404:
            raise
    else:
        raise ValueError(
            "The grant PDF pages must be inaccessible through the publication version"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", required=True)
    parser.add_argument("--compose-project", required=True)
    args = parser.parse_args()
    url = urlsplit(args.api)
    if not (
        url.scheme == "http"
        and url.hostname == "127.0.0.1"
        and url.port
        and url.path in {"", "/"}
        and not (url.query or url.fragment or url.username)
    ):
        parser.error("--api must be an isolated HTTP loopback origin")
    smoke(args.api, args.compose_project)
