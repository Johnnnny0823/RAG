"""Recover a bounded range of TIPO issues from the official archive."""

import argparse
import json
import re
from ftplib import all_errors
from os import getenv

from services.ingestion.download import list_archive_issues
from services.ingestion.latest_publication import main as import_one


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("publication", "grant"), required=True)
    parser.add_argument("--year", required=True)
    parser.add_argument("--from-issue", required=True)
    parser.add_argument("--through-issue", required=True)
    parser.add_argument("--limit", type=int, default=100, help="Documents per issue")
    parser.add_argument(
        "--index-mode", choices=("none", "lexical", "hybrid"), default="lexical"
    )
    parser.add_argument("--objects", default=getenv("PATENT_OBJECTS_DIR"))
    parser.add_argument("--fulltext", action="store_true")
    parser.add_argument("--dates", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    first, last = args.from_issue, args.through_issue
    if (
        not re.fullmatch(r"[0-9]{3}", args.year)
        or not all(re.fullmatch(r"[0-9]{6}", issue) for issue in (first, last))
        or first[:3] != last[:3]
        or not 0 <= int(last) - int(first) < 20
    ):
        parser.error(
            "Specify 1 to 20 consecutive issues in one volume and archive year"
        )
    if not 1 <= args.limit <= 500:
        parser.error("--limit must be between 1 and 500")
    if args.apply and not args.objects:
        parser.error("--apply requires --objects or PATENT_OBJECTS_DIR")

    try:
        available = set(list_archive_issues(args.stage, args.year))
        requested = [f"{number:06d}" for number in range(int(first), int(last) + 1)]
        missing = [issue for issue in requested if issue not in available]
        if missing:
            raise ValueError(f"Issues missing from the archive: {', '.join(missing)}")
    except (*all_errors, ValueError) as error:
        parser.exit(1, f"TIPO archive could not be verified: {error}\n")

    print(
        json.dumps(
            {
                "stage": args.stage,
                "year": args.year,
                "issues": requested,
                "documents_per_issue": args.limit,
                "apply": args.apply,
            }
        ),
        flush=True,
    )
    if not args.apply:
        return 0

    options = [
        "--apply",
        "--issue-year",
        args.year,
        "--objects",
        args.objects,
        "--limit",
        str(args.limit),
        "--index-mode",
        args.index_mode,
    ]
    if args.stage == "grant":
        options.append("--grants")
    if args.fulltext:
        options.extend(["--archive-year", args.year])
    if args.dates:
        options.extend(["--gazette-year", args.year])
    for issue in requested:
        try:
            status = import_one([*options, "--archive-issue", issue])
        except SystemExit as error:
            parser.exit(1, f"Archive backfill stopped at {issue}: {error.code}\n")
        if status:
            print(f"Archive backfill stopped at {issue}", flush=True)
            return status
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
