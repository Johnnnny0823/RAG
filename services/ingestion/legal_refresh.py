"""Verify and refresh supported events from the latest official TIPO gazette."""

import argparse
import hashlib
import json
import re
from collections import Counter
from ftplib import all_errors
from xml.etree.ElementTree import ParseError

from services.ingestion.artifacts import LocalObjectStore, add_objects_argument
from services.ingestion.download import (
    ARCHIVES,
    LEGAL_INDEX_URL,
    download_ftps_xml,
    download_legal_index,
    list_archive_issues,
)
from services.ingestion.issue_manifest import HOST
from services.ingestion.legal_events import (
    TYPES,
    archive_url,
    import_events,
    parse_events,
)
from services.ingestion.patentpub import parse_xml


def refresh(year: str, store: LocalObjectStore, *, apply: bool) -> dict:
    index = download_legal_index()
    root = parse_xml(index)
    if (
        root.tag != "SundryData"
        or not len(root)
        or root.get("total-count") != str(len(root))
        or any(row.tag != "Sundry" or not row.get("sudtype") for row in root)
    ):
        raise ValueError("Expected a complete official TIPO event index")

    folder = ARCHIVES["legal"]
    for issue in reversed(list_archive_issues("legal", year)[-8:]):
        index_url = f"{HOST}/{folder}/{year}/{folder}_{issue}/index.xml"
        if download_ftps_xml(index_url) == index:
            break
    else:
        raise ValueError(
            "Official TIPO event index did not match a recent archive issue"
        )

    payloads = {}
    for event_type in TYPES:
        expected = Counter(
            (row.get("aplno"), row.get("cerno"))
            for row in root
            if row.get("sudtype") == event_type
            and re.fullmatch(r"I[0-9]+", row.get("cerno", ""))
        )
        if not expected:
            continue
        payload = download_ftps_xml(archive_url(year, issue, event_type))
        events = parse_events(payload, issue, event_type)
        if Counter((e.application_no, e.certificate_no) for e in events) != expected:
            raise ValueError(
                f"Official event category {event_type} disagrees with its index"
            )
        payloads[event_type] = (payload, len(events))

    if apply:
        store.put(index)
    return {
        "index_url": LEGAL_INDEX_URL,
        "archive_index_url": index_url,
        "issue": issue,
        "index_sha256": hashlib.sha256(index).hexdigest(),
        "apply": apply,
        "events": {
            event_type: import_events(payload, store, year, issue, event_type)
            if apply
            else {
                "invention_events": count,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            for event_type, (payload, count) in payloads.items()
        },
    }


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", required=True)
    parser.add_argument("--apply", action="store_true")
    add_objects_argument(parser)
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[0-9]{3}", args.year):
        parser.error("--year must be a three-digit ROC archive year")
    try:
        result = refresh(args.year, LocalObjectStore(args.objects), apply=args.apply)
    except (*all_errors, ValueError, ParseError) as error:
        parser.exit(1, f"TIPO event refresh could not be verified: {error}\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
