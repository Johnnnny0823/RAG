"""Discover the latest TIPO invention publication issue and optionally import it."""

import argparse
import hashlib
import json
from os import getenv
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import ParseError

from services.ingestion.download import INDEX_URL, download_publication_index
from services.ingestion.import_issue import parse_import_args
from services.ingestion.issue_index import discover_issue
from services.ingestion.run_pipeline import run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="Import the discovered issue"
    )
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument(
        "--index-mode", choices=("none", "lexical", "hybrid"), default="lexical"
    )
    parser.add_argument("--objects", type=Path, default=getenv("PATENT_OBJECTS_DIR"))
    args = parser.parse_args()
    if not 1 <= args.limit <= 500:
        parser.error("--limit must be between 1 and 500")
    if args.apply and args.objects is None:
        parser.error("--apply requires --objects or PATENT_OBJECTS_DIR")
    try:
        data = download_publication_index()
        issue, total_records = discover_issue(data)
    except (OSError, ParseError, ValueError) as error:
        parser.exit(1, f"TIPO latest publication could not be verified: {error}\n")

    print(
        json.dumps(
            {
                "source": INDEX_URL,
                "issue": issue,
                "sha256": hashlib.sha256(data).hexdigest(),
                "available_records": total_records,
                "selected_records": min(total_records, args.limit),
                "content_scope": "metadata_and_abstract",
                "apply": args.apply,
            }
        ),
        flush=True,
    )
    if not args.apply:
        return 0

    with TemporaryDirectory(prefix="patentscope-latest-publication-") as temporary:
        index = Path(temporary) / "index.xml"
        index.write_bytes(data)
        imported = parse_import_args(
            [
                "--verified-tipo",
                "--index",
                str(index),
                "--index-source-url",
                INDEX_URL,
                "--batch",
                issue,
                "--limit",
                str(args.limit),
                "--objects",
                str(args.objects),
            ]
        )
        return run_pipeline(imported, args.index_mode, batch_size=24, timeout=90)


if __name__ == "__main__":
    raise SystemExit(main())
