"""Verify two official JPEGs in an isolated Compose project with 053030 grants."""

import argparse
import hashlib
import subprocess
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import urlopen

from scripts.evaluate_search import request

CASES = (
    (
        "M688679",
        3,
        "adef492f39db89c809115dd68d028cbff178a3634fbcf11f38de3ab0739c3093",
        "f8501044f813b2d3881fad354fea3b0ad514776ceeb25eba9f105330c031e091",
    ),
    (
        "D247328",
        1,
        "f8c18dc5cb114fc70bd54b38a4cd8ea97b57772adac3568603e88c36c3e83d18",
        "b5fccaeee7ef7896fae9e4c6e17408877c07ddcf3c6c55e39b0b10638a26de48",
    ),
)


def smoke(api: str, project: str):
    compose = [
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
        "services.ingestion.grant_drawing",
    ]
    for number, position, specification, checksum in CASES:
        full, index = request(api, f"/patents?number={number}&number_type=grant")[
            "items"
        ]
        assert (
            full["content_scope"] == "fulltext" and index["content_scope"] != "fulltext"
        )
        options = [
            "--specification-sha256",
            specification,
            "--figure",
            str(position),
            "--expected-sha256",
            checksum,
        ]
        denied = subprocess.run(
            [*compose, *options, "--apply-to", index["document_id"]],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert (
            denied.returncode == 1
            and "No matching official specification" in denied.stderr
        ), denied.stderr
        for _ in range(2):
            subprocess.run(
                [*compose, *options, "--apply-to", full["document_id"]],
                check=True,
                timeout=150,
            )
        path = f"/patents/{full['document_id']}"
        detail = request(api, path)
        [source] = [
            item for item in detail["sources"] if item["artifact_sha256"] == checksum
        ]
        assert (
            source["record_locator"]
            == f"/specification/drawings/figure[{position}]/img[1]"
        )
        with urlopen(
            api + "/api/v1" + path + "/drawings/" + checksum, timeout=10
        ) as response:
            assert response.headers.get_content_type() == "image/jpeg"
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert hashlib.sha256(response.read()).hexdigest() == checksum
        try:
            urlopen(
                f"{api}/api/v1/patents/{index['document_id']}/drawings/{checksum}",
                timeout=10,
            )
        except HTTPError as error:
            assert error.code == 404
        else:
            raise AssertionError(
                "Drawing was accessible through the index-only version"
            )
        print(
            f"{number}: verified official JPEG, source locator and version boundaries"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", required=True)
    parser.add_argument("--compose-project", required=True)
    args = parser.parse_args()
    origin = urlsplit(args.api)
    if (
        origin.scheme != "http"
        or origin.hostname != "127.0.0.1"
        or not origin.port
        or origin.path not in {"", "/"}
        or origin.username
        or origin.query
        or origin.fragment
    ):
        parser.error("--api must be an isolated HTTP loopback origin")
    smoke(args.api.rstrip("/"), args.compose_project)
