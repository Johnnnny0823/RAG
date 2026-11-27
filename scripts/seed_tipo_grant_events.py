"""Prepare checksum-pinned TIPO grants, corrections and extinguishments for E2E."""

import argparse
import subprocess
from pathlib import Path

from scripts.seed_tipo_e2e import GRANT_SHA256, GRANT_URL, IMPORT, RUN, prepare
from services.ingestion.legal_events import archive_url

UTILITY_INDEX = (
    "ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/"
    "PatentIsuRegSpecXMLA_053010/index.xml"
)
EVENT_CHECKSUMS = {
    "sud08": "213b98e7337a0f99b74b9eff59ce0d92f0f27ccecf665892f8ee48b8423bd964",
    "sud24": "97993734e1cd87b54537069ded8593a02615d7aa09442779a47a688ccffc16a3",
}
GRANTS = (
    (
        "053010",
        "M681479",
        UTILITY_INDEX,
        "5f2bed1abaa7b9e812fcf1f1e2b240007c4881be719fb387d114b4ca92611d2e",
    ),
    ("053028", "D246955", GRANT_URL, GRANT_SHA256),
    (
        "053030",
        "M688686",
        "ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/PatentIsuRegSpecXMLA_053030/index.xml",
        "9bb410efd13450866eaa0bc34523fce8785c46d11ce7237efee4cd0c3b3727f0",
    ),
    (
        "052006",
        "D236497",
        "ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/114/PatentIsuRegSpecXMLA_052006/index.xml",
        "99cde994594aa622cf9469ecb6541403b3567b4597342a6915c35ce5dab526f8",
    ),
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
    for event_type, checksum in EVENT_CHECKSUMS.items():
        prepare(
            cache / f"{event_type}.xml",
            archive_url("115", "053033", event_type),
            checksum,
            offline=args.offline,
        )
    if args.prepare_only:
        return

    # Import the immutable event first so E2E exercises late linking on grant import.
    run = [*RUN, "-v", f"{cache}:/inputs:ro"]
    for event_type in EVENT_CHECKSUMS:
        subprocess.run(
            [
                *run,
                "migrate",
                "python",
                "-c",
                "import os\nimport sys\nfrom pathlib import Path\n"
                "from services.ingestion.artifacts import LocalObjectStore\n"
                "from services.ingestion.legal_events import import_events\n"
                "event_type = sys.argv[1]\n"
                "data = Path(f'/inputs/{event_type}.xml').read_bytes()\n"
                "store = LocalObjectStore(Path(os.environ['PATENT_OBJECTS_DIR']))\n"
                "print(import_events(data, store, '115', '053033', event_type))",
                event_type,
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
