"""Seed the dedicated Playwright Compose project with pinned official patents.

The corpus is rebuilt from archived TIPO issues only: 100 publication records of
issue 024019 (17 with full text) and the grant of one of them from issue 053028.
"""

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

from services.ingestion.download import download_ftps_xml

ARCHIVE = "ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019"
INDEX_URL = f"{ARCHIVE}/index.xml"
MANIFEST_URL = f"{ARCHIVE}/index_all.xml"
SPEC_URL = f"{ARCHIVE}/2419202639611/113133932-A0304.xml"
GRANT_URL = "ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/PatentIsuRegSpecXMLA_053028/index.xml"
INDEX_SHA256 = "7befed78be2cc6067266f13afd4a34f6feca4730b9a717f3f99890d551da9b69"
MANIFEST_SHA256 = "2b338d71f59e0de4d987bd3651f0b9044f64182fab6bcda664beae57467a728f"
SPEC_SHA256 = "0537aedd633f9c63e7fe06790732cb0bf06e240e0bebf360c725abf9bc98d70a"
GRANT_SHA256 = "60936a7ab763fbb8bd79b8a3071aa89d43da3ffe4ef65928734a9ddc70827a4a"
# Specifications of the first 20 records in the issue index, as listed by index_all.xml.
MANIFEST_SPECS = {
    "2419202639291/114109775-A0304.xml": "0c67d45d0a556b97aa24e735bd5a4f05ce4fbbf640b6f891046cf525c0472634",
    "2419202639320/114101433-A0304.xml": "768f032256d1fd80caa90e76421e6738f0d359f2704bbf06d43f43fedf186763",
    "2419202639327/114108308-A0304.xml": "2a279ebee063c9bb5345dd3f0023adb3a7a7a199a6deedaaa54c9795fecda608",
    "2419202639396/114100651-A0304.xml": "5ef8785f593905a48656491372cb38dd6ce447444abeef21f8b1489c638fc6ea",
    "2419202639427/113139336-A0304.xml": "5d7598a6e8a8b60ff4ace80ab047f7c22e96d6707fe9244b8cd3543c30b7bd17",
    "2419202639442/114100774-A0304.xml": "c58e0b450d5ff2fe9e7bfd7887b747a4b1d8c88f02fb4344cfbcc3f3dc8536e6",
    "2419202639448/114109735-A0304.xml": "77ae3a1674a18b5d3505014f10b814ea835887616b8a1df782ddbdc9036306ef",
    "2419202639611/113133932-A0304.xml": SPEC_SHA256,
    "2419202639803/114109778-A0304.xml": "7e8ba9700cc5de40d4e0677e62e935a6e7ee0456fd9f5093df332db96f744178",
    "2419202640162/114106690-A0304.xml": "838091d244ebaf021106f9efa390c33beb4140a92590b9fbe613c5ed5937d047",
    "2419202640273/114109719-A0304.xml": "601dbe1f92e25921c402ea16db4204dcec281245d1d02a49477b27e6127de95b",
    "2419202640295/113150273-A0304.xml": "e8d2c092e79d2071dea8a510652d926d42e108e4578298b2b5f9d00d256da844",
    "2419202640441/114109708-A0304.xml": "7bc1f3224eeefd14d47fb3811c68868cece44edcd0989985ce99ab70af32e725",
    "2419202640537/114109785-A0304.xml": "f6261f0d3acd7bc906aecec9160522d0f512a0f0de43c6f1f9bd44ee8c0e0ec4",
    "2419202640647/114109761-A0304.xml": "e486ed5590590da6fe59689fb4d47df59dcc163b421a5aa21f3903955b025543",
    "2419202640851/114109786-A0304.xml": "9c588784318e1064eccda446251a8699ebd5b867aa7365187e149188e4fe8d3d",
    "2419202640910/114106310-A0304.xml": "19243125634c86a4d3dc93249fddec313c6accb22bccdf591054798e6546e253",
    "2419202640989/114104452-A0304.xml": "ebbb91c5de33e39f62d2f6ac825e84b5db3dc1abb90dafbf47f70806ad45ec0b",
    "2419202641133/114109759-A0304.xml": "aca4c4d603d6807c212c0ef9139668d00a1da4b8cba66f332bb9d1c0d39df83e",
    "2419202641358/114109720-A0304.xml": "9781720488530b447dfc4d9c1fe458e9fa061828c70c946b71f86a0ef7d4b6c6",
}
COMPOSE = [
    "docker",
    "compose",
    "--env-file",
    ".env.example",
    "-p",
    os.environ.get("COMPOSE_PROJECT_NAME", "patentscope-tipo-e2e"),
]
RUN = [*COMPOSE, "run", "--rm", "--no-deps"]
IMPORT = [
    "migrate",
    "python",
    "-m",
    "services.ingestion.import_issue",
    "--verified-tipo",
]
VERIFY = ["migrate", "python", "-m", "services.ingestion.verify_document"]
OBJECTS = ["--objects", "/inputs/objects"]
# Three of the 20 official specifications lack claim numbers and stay quarantined.
EXPECTED = (
    {"fulltext": 1, "metadata": 99, "invalid_records": 0, "quarantined_specs": 0},
    {
        "fulltext": 17,
        "metadata": 3,
        "invalid_records": 0,
        "quarantined_specs": 3,
        "download_failures": [],
    },
    {
        "fulltext": 0,
        "metadata": 0,
        "invalid_records": 0,
        "quarantined_specs": 0,
        "grants_with_claims": 1,
    },
)


def prepare(path: Path, url: str, expected: str, *, offline: bool) -> bool:
    if path.exists():
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != expected:
            raise ValueError(f"Cached fixture has an unexpected SHA-256: {path}")
        return False
    if offline:
        raise FileNotFoundError(path)
    payload = download_ftps_xml(url)
    if hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError(f"Official fixture has an unexpected SHA-256: {url}")
    with path.open("xb") as stream:
        stream.write(payload)
    return True


def check_import(output: str, expected: dict) -> dict:
    """Reject an import whose counts differ, whether it was new or reused."""
    result = json.loads(output.strip().splitlines()[-1])
    counts = {
        key: value for key, value in result.items() if key not in {"status", "reused"}
    }
    if counts != expected:
        raise ValueError(f"Unexpected import result: {result}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    cache = args.cache.resolve()
    # import_issue reads manifest downloads from this cache, keyed by source URL.
    downloads = cache / "objects" / "download-cache" / MANIFEST_SHA256
    downloads.mkdir(parents=True, exist_ok=True)
    fixtures = [
        (cache / "index.xml", INDEX_URL, INDEX_SHA256),
        (cache / "index_all.xml", MANIFEST_URL, MANIFEST_SHA256),
        (cache / "spec.xml", SPEC_URL, SPEC_SHA256),
        (cache / "grant-053028.xml", GRANT_URL, GRANT_SHA256),
    ]
    for relative, checksum in MANIFEST_SPECS.items():
        url = f"{ARCHIVE}/{relative}"
        fixtures.append(
            (downloads / hashlib.sha256(url.encode()).hexdigest(), url, checksum)
        )
    for path, url, checksum in fixtures:
        if prepare(path, url, checksum, offline=args.offline):
            time.sleep(1)

    volume = ["-v", f"{cache}:/inputs"]
    read_only = ["-v", f"{cache}:/inputs:ro"]
    publication = [
        "--index",
        "/inputs/index.xml",
        "--index-source-url",
        INDEX_URL,
        "--batch",
        "024019",
    ]
    imports = [
        [
            *publication,
            "--spec",
            "202639611=/inputs/spec.xml",
            "--limit",
            "100",
        ],
        [
            *publication,
            "--manifest",
            "/inputs/index_all.xml",
            "--manifest-url",
            MANIFEST_URL,
            "--limit",
            "20",
            "--cache-only",
        ],
        [
            "--index",
            "/inputs/grant-053028.xml",
            "--index-source-url",
            GRANT_URL,
            "--grant-number",
            "I941082",
            "--batch",
            "053028",
        ],
    ]
    for options, expected in zip(imports, EXPECTED, strict=True):
        done = subprocess.run(
            [*RUN, *volume, *IMPORT, *options, *OBJECTS],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        print(json.dumps(check_import(done.stdout, expected), ensure_ascii=False))
    commands = [
        [*RUN, *read_only, *VERIFY, "202639611", *OBJECTS],
        [*RUN, *read_only, *VERIFY, "202640162", *OBJECTS],
        [*RUN, *read_only, *VERIFY, "I941082", "--grant-issue", "053028", *OBJECTS],
        [*RUN, "migrate", "python", "-m", "services.retrieval.index_lexical"],
        [*RUN, "migrate", "python", "-m", "services.retrieval.index_semantic"],
    ]
    for command in commands:
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
