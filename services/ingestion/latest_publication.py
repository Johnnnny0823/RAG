"""Discover the latest TIPO invention publication issue and optionally import it."""

import argparse
import hashlib
import json
import re
from ftplib import all_errors
from os import getenv
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import ParseError

from services.ingestion.download import (
    INDEX_URL,
    download_ftps_xml,
    download_publication_index,
)
from services.ingestion.import_issue import parse_import_args
from services.ingestion.issue_index import discover_issue, parse_issue_index
from services.ingestion.issue_manifest import HOST, resolve_spec_urls
from services.ingestion.run_pipeline import run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="Import the discovered issue"
    )
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument(
        "--archive-year",
        help="Official three-digit ROC archive year for full specifications",
    )
    parser.add_argument(
        "--index-mode", choices=("none", "lexical", "hybrid"), default="lexical"
    )
    parser.add_argument("--objects", type=Path, default=getenv("PATENT_OBJECTS_DIR"))
    args = parser.parse_args()
    if not 1 <= args.limit <= 500:
        parser.error("--limit must be between 1 and 500")
    if args.apply and args.objects is None:
        parser.error("--apply requires --objects or PATENT_OBJECTS_DIR")
    if args.archive_year is not None and not re.fullmatch(
        r"[0-9]{3}", args.archive_year
    ):
        parser.error("--archive-year must be a three-digit ROC year")

    manifest = None
    try:
        data = download_publication_index()
        issue, total_records = discover_issue(data)
        if args.archive_year is not None:
            manifest_url = (
                f"{HOST}/InventionPubXML/{args.archive_year}"
                f"/InventionPubXML_{issue}/index_all.xml"
            )
            manifest = download_ftps_xml(manifest_url)
            records, invalid = parse_issue_index(data, args.limit, issue)
            if invalid:
                raise ValueError(
                    "Invalid selected publication records in the latest index"
                )
            resolve_spec_urls(
                manifest,
                manifest_url,
                issue,
                {record.publication_no: record.application_no for record in records},
            )
    except (*all_errors, ParseError, ValueError) as error:
        parser.exit(1, f"TIPO latest publication could not be verified: {error}\n")

    print(
        json.dumps(
            {
                "source": INDEX_URL,
                "issue": issue,
                "sha256": hashlib.sha256(data).hexdigest(),
                "available_records": total_records,
                "selected_records": min(total_records, args.limit),
                "requested_scope": "fulltext" if manifest else "metadata_and_abstract",
                **(
                    {
                        "manifest_url": manifest_url,
                        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
                    }
                    if manifest
                    else {}
                ),
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
        options = [
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
        if manifest:
            manifest_path = Path(temporary) / "index_all.xml"
            manifest_path.write_bytes(manifest)
            options.extend(
                ["--manifest", str(manifest_path), "--manifest-url", manifest_url]
            )
        return run_pipeline(
            parse_import_args(options),
            args.index_mode,
            batch_size=24,
            timeout=90,
            require_complete=bool(manifest),
        )


if __name__ == "__main__":
    raise SystemExit(main())
