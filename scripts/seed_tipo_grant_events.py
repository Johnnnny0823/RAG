"""Prepare two checksum-pinned TIPO grants and their official corrections for E2E."""

import argparse
import subprocess
from pathlib import Path

from scripts.seed_tipo_e2e import GRANT_SHA256, GRANT_URL, IMPORT, RUN, prepare
from services.ingestion.legal_events import archive_url

UTILITY_INDEX = (
    "ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/"
    "PatentIsuRegSpecXMLA_053010/index.xml"
)
CORRECTION_SHA256 = "97993734e1cd87b54537069ded8593a02615d7aa09442779a47a688ccffc16a3"
GRANTS = (
    (
        "053010",
        "M681479",
        UTILITY_INDEX,
        "5f2bed1abaa7b9e812fcf1f1e2b240007c4881be719fb387d114b4ca92611d2e",
    ),
    ("053028", "D246955", GRANT_URL, GRANT_SHA256),
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    cache = args.cache.resolve()
    cache.mkdir(parents=True, exist_ok=True)
    for issue, _, url, checksum in GRANTS:
        prepare(cache / f"grant-{issue}.xml", url, checksum, offline=args.offline)
    prepare(
        cache / "sud24.xml",
        archive_url("115", "053033", "sud24"),
        CORRECTION_SHA256,
        offline=args.offline,
    )
    if args.prepare_only:
        return

    # Import the immutable event first so E2E exercises late linking on grant import.
    run = [*RUN, "-v", f"{cache}:/inputs:ro"]
    subprocess.run(
        [
            *run,
            "migrate",
            "python",
            "-c",
            "import os\nfrom pathlib import Path\n"
            "from services.ingestion.artifacts import LocalObjectStore\n"
            "from services.ingestion.legal_events import import_events\n"
            "data = Path('/inputs/sud24.xml').read_bytes()\n"
            "print(import_events(data, LocalObjectStore(Path(os.environ['PATENT_OBJECTS_DIR'])),"
            " '115', '053033', 'sud24'))",
        ],
        check=True,
    )
    for issue, certificate, url, _ in GRANTS:
        subprocess.run(
            [
                *run,
                *IMPORT,
                "--index",
                f"/inputs/grant-{issue}.xml",
                "--index-source-url",
                url,
                "--batch",
                issue,
                "--grant-number",
                certificate,
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
