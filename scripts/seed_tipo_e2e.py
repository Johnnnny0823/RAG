"""Seed the dedicated Playwright Compose project with one pinned official patent."""

import argparse
import hashlib
import subprocess
import time
from pathlib import Path

from services.ingestion.download import download_ftps_xml

ARCHIVE = "ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019"
INDEX_URL = f"{ARCHIVE}/index.xml"
SPEC_URL = f"{ARCHIVE}/2419202639611/113133932-A0304.xml"
INDEX_SHA256 = "7befed78be2cc6067266f13afd4a34f6feca4730b9a717f3f99890d551da9b69"
SPEC_SHA256 = "0537aedd633f9c63e7fe06790732cb0bf06e240e0bebf360c725abf9bc98d70a"
COMPOSE = [
    "docker",
    "compose",
    "--env-file",
    ".env.example",
    "-p",
    "patentscope-tipo-e2e",
]


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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    cache = args.cache.resolve()
    cache.mkdir(parents=True, exist_ok=True)
    if prepare(cache / "index.xml", INDEX_URL, INDEX_SHA256, offline=args.offline):
        time.sleep(1)
    prepare(cache / "spec.xml", SPEC_URL, SPEC_SHA256, offline=args.offline)

    run = [*COMPOSE, "run", "--rm", "--no-deps"]
    volume = ["-v", f"{cache}:/inputs"]
    commands = [
        [
            *run,
            *volume,
            "migrate",
            "python",
            "-m",
            "services.ingestion.import_issue",
            "--verified-tipo",
            "--index",
            "/inputs/index.xml",
            "--index-source-url",
            INDEX_URL,
            "--spec",
            "202639611=/inputs/spec.xml",
            "--batch",
            "024019",
            "--limit",
            "1",
            "--objects",
            "/inputs/objects",
        ],
        [
            *run,
            "-v",
            f"{cache}:/inputs:ro",
            "migrate",
            "python",
            "-m",
            "services.ingestion.verify_document",
            "202639611",
            "--objects",
            "/inputs/objects",
        ],
        [*run, "migrate", "python", "-m", "services.retrieval.index_lexical"],
        [*run, "migrate", "python", "-m", "services.retrieval.index_semantic"],
    ]
    for command in commands:
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
