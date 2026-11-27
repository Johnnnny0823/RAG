"""Import a bounded sample from a verified TIPO issue index and its XML specs."""

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from psycopg.types.json import Jsonb
from sqlalchemy.engine import Connection

from services.api.db import engine
from services.ingestion.artifacts import (
    MAX_GAZETTE_XML_BYTES,
    MAX_XML_BYTES,
    LocalObjectStore,
    RawArtifact,
    add_objects_argument,
)
from services.ingestion.grant_index import parse_selected_grants
from services.ingestion.download import (
    GRANT_INDEX_URL,
    INDEX_URL as PUBLICATION_INDEX_URL,
)
from services.ingestion.claim_references_v1 import INSERT_REFERENCES, reference_pairs
from services.ingestion.issue_index import parse_issue_index
from services.ingestion.issue_manifest import fetch_specifications, resolve_spec_urls
from services.ingestion.legal_linking import link_events
from services.ingestion.patentpub import PatentPublication
from services.ingestion.specification import Claim, Section, parse_specification

PARSER_VERSION = "tipo-issue-1"
DATASET_URL = "https://data.gov.tw/dataset/15996"
LICENSE_URL = "https://data.gov.tw/license"


def validate_index_source(url: str, batch: str, *, grant: bool) -> None:
    if url == (GRANT_INDEX_URL if grant else PUBLICATION_INDEX_URL):
        return
    dataset = "PatentIsuRegSpecXMLA" if grant else "InventionPubXML"
    archived = re.fullmatch(
        rf"ftps://ftp\.tipo\.gov\.tw/{dataset}/[0-9]{{3}}/{dataset}_([0-9]{{6}})/index\.xml",
        url,
    )
    if archived is None or archived[1] != batch:
        raise ValueError("Index source URL must match the official dataset and issue")


@dataclass(frozen=True)
class Specification:
    artifact: RawArtifact
    sections: list[Section]
    claims: list[Claim]


def read_xml(path: Path, *, size_limit: int = MAX_XML_BYTES) -> bytes:
    with path.open("rb") as stream:
        payload = stream.read(size_limit + 1)
    if len(payload) > size_limit:
        raise ValueError(f"{path.name} exceeds the XML size limit")
    return payload


def insert_artifact(conn, batch_id, locator, raw, status, errors=None):
    return conn.exec_driver_sql(
        """INSERT INTO ingestion_artifacts
           (batch_id, source_locator, checksum, object_key, size_bytes, status, error_log)
           VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (
            batch_id,
            locator,
            raw.checksum,
            raw.object_key,
            raw.size_bytes,
            status,
            errors,
        ),
    ).scalar_one()


def store_document(
    conn: Connection,
    record: PatentPublication,
    jurisdiction: str,
    spec: Specification | None,
    *,
    stage: str = "publication",
):
    application_key = (jurisdiction, record.application_no)
    conn.exec_driver_sql(
        """INSERT INTO patent_applications (jurisdiction, application_no, filing_date)
           VALUES (%s,%s,%s) ON CONFLICT (jurisdiction, application_no) DO NOTHING""",
        (*application_key, record.filing_date),
    )
    application_id = conn.exec_driver_sql(
        "SELECT id FROM patent_applications WHERE jurisdiction = %s AND application_no = %s",
        application_key,
    ).scalar_one()

    source_hash = record.source_hash
    has_fulltext = spec is not None and bool(spec.sections)
    if spec is not None and has_fulltext:
        source_hash = hashlib.sha256(
            f"{source_hash}:{spec.artifact.checksum}".encode()
        ).hexdigest()
    key = (jurisdiction, record.publication_no, source_hash, PARSER_VERSION, stage)
    document_id = conn.exec_driver_sql(
        """INSERT INTO patent_documents
           (jurisdiction, publication_no, source_hash, parser_version,
            document_stage, application_id, kind_code, publication_date, title_zh, title_en,
            abstract_zh, abstract_en, metadata_jsonb)
           VALUES (%s,%s,%s,%s,%s,%s,'',%s,%s,%s,%s,%s,%s)
           ON CONFLICT (jurisdiction, document_stage, publication_no, kind_code,
                        source_hash, parser_version) DO NOTHING RETURNING id""",
        (
            *key,
            application_id,
            record.publication_date,
            record.title_zh,
            record.title_en,
            record.abstract_zh,
            record.abstract_en,
            Jsonb(
                {
                    "applicants": record.applicants,
                    "inventors": record.inventors,
                    "content_scope": "fulltext"
                    if has_fulltext
                    else (
                        "claims_only"
                        if spec and spec.claims
                        else "metadata_and_abstract"
                    ),
                }
            ),
        ),
    ).scalar_one_or_none()
    if document_id is None:
        return conn.exec_driver_sql(
            """SELECT id FROM patent_documents WHERE jurisdiction = %s AND publication_no = %s
               AND source_hash = %s AND parser_version = %s
               AND document_stage = %s AND kind_code = ''""",
            key,
        ).scalar_one()

    for code, version in sorted(set(record.ipc)):
        conn.exec_driver_sql(
            """INSERT INTO patent_classifications (document_id, scheme, code, version)
               VALUES (%s,'IPC',%s,%s)""",
            (document_id, code, version),
        )
    if spec is not None:
        for section in spec.sections:
            conn.exec_driver_sql(
                """INSERT INTO patent_sections
                   (document_id, section_type, ordinal, original_text, source_locator_jsonb)
                   VALUES (%s,%s,%s,%s,%s)""",
                (
                    document_id,
                    section.kind,
                    section.ordinal,
                    section.text,
                    Jsonb(
                        {
                            "xpath": section.locator,
                            "artifact_sha256": spec.artifact.checksum,
                        }
                    ),
                ),
            )
        for claim in spec.claims:
            conn.exec_driver_sql(
                """INSERT INTO patent_claims
                   (document_id, claim_number, text, independent_flag_nullable, source_locator_jsonb)
                   VALUES (%s,%s,%s,%s,%s)""",
                (
                    document_id,
                    claim.number,
                    claim.text,
                    claim.independent,
                    Jsonb(
                        {
                            "xpath": claim.locator,
                            "artifact_sha256": spec.artifact.checksum,
                        }
                    ),
                ),
            )
        pairs = reference_pairs((claim.number, claim.text) for claim in spec.claims)
        if pairs:
            conn.exec_driver_sql(
                INSERT_REFERENCES,
                [(document_id, child, parent) for child, parent in pairs],
            )
    return document_id


def link_artifact(conn, document_id, artifact_id, locator):
    conn.exec_driver_sql(
        """INSERT INTO document_artifacts (document_id, artifact_id, record_locator)
           VALUES (%s,%s,%s) ON CONFLICT DO NOTHING""",
        (document_id, artifact_id, locator),
    )


def import_issue(args):
    store = LocalObjectStore(args.objects)
    data = read_xml(
        args.index,
        size_limit=MAX_GAZETTE_XML_BYTES if args.grant_number else MAX_XML_BYTES,
    )
    index_raw = store.put(data)
    index_error = None
    grant_claims = {}
    try:
        if args.grant_number:
            grants = parse_selected_grants(data, args.batch, args.grant_number)
            records, issues = [grant for grant, _ in grants], []
            grant_claims = {grant.publication_no: claims for grant, claims in grants}
        else:
            records, issues = parse_issue_index(
                data, args.limit, None if args.demo else args.batch
            )
        if not records:
            index_error = "No usable records in selected issue range"
    except (ValueError, ET.ParseError) as error:
        records, issues, index_error = [], [], str(error)

    sources = {}
    failures = {}
    official_manifest = None
    specs = args.specs
    if args.manifest:
        if index_error or issues:
            raise ValueError(
                "A valid issue index is required before fetching specifications"
            )
        manifest_data = read_xml(
            args.manifest,
            size_limit=MAX_GAZETTE_XML_BYTES if args.grant_number else MAX_XML_BYTES,
        )
        sources = resolve_spec_urls(
            manifest_data,
            args.manifest_url,
            args.batch,
            {record.publication_no: record.application_no for record in records},
            grant=bool(args.grant_number),
        )
        official_manifest = store.put(manifest_data)
        cache = args.objects / "download-cache" / official_manifest.checksum
        cache.mkdir(parents=True, exist_ok=True)
        specs, failures = fetch_specifications(
            sources, cache, cache_only=args.cache_only
        )
        if args.fetch_only:
            return {
                "status": "partial" if failures else "complete",
                "downloaded_or_cached": len(specs),
                "download_failures": failures,
            }
    specs_raw = {number: store.put(read_xml(path)) for number, path in specs.items()}
    manifest = {
        "index": index_raw.checksum,
        "limit": args.limit,
        "specs": {number: raw.checksum for number, raw in specs_raw.items()},
    }
    if args.index_source_url:
        manifest["index_source_url"] = args.index_source_url
    if len(args.grant_number) == 1:
        manifest["grant_number"] = args.grant_number[0]
    elif args.grant_number:
        manifest["grant_numbers"] = sorted(args.grant_number)
    if official_manifest is not None:
        manifest.update(
            official_manifest=official_manifest.checksum,
            manifest_url=args.manifest_url,
            failures=failures,
        )
    checksum = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()

    jurisdiction = "DEMO" if args.demo else "TW"
    dataset_key, dataset_name, dataset_url = (
        ("DEMO-issue-index", "DEMO fixture", None)
        if args.demo
        else (
            "TIPO-15987",
            "專利說明書(1案1XML檔)",
            "https://data.gov.tw/dataset/15987",
        )
        if args.grant_number
        else ("TIPO-15996", "發明公開說明書(1案1XML檔)", DATASET_URL)
    )
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """INSERT INTO source_datasets
               (dataset_key, name, publisher, official_url, license_notes, checked_at, is_demo)
               VALUES (%s,%s,%s,%s,%s,'2026-11-09T00:00:00+08:00',%s)
               ON CONFLICT (dataset_key) DO NOTHING""",
            (
                dataset_key,
                dataset_name,
                "DEMO" if args.demo else "經濟部智慧財產局",
                dataset_url,
                None if args.demo else LICENSE_URL,
                args.demo,
            ),
        )
        dataset_id = conn.exec_driver_sql(
            "SELECT id FROM source_datasets WHERE dataset_key = %s", (dataset_key,)
        ).scalar_one()
        batch_key = (dataset_id, args.batch, checksum, PARSER_VERSION)
        batch_id = conn.exec_driver_sql(
            """INSERT INTO ingestion_batches (dataset_id, batch_key, checksum, parser_version, status)
               VALUES (%s,%s,%s,%s,'processing') ON CONFLICT DO NOTHING RETURNING id""",
            batch_key,
        ).scalar_one_or_none()
        if batch_id is None:
            result = conn.exec_driver_sql(
                """SELECT status, counts_jsonb FROM ingestion_batches WHERE dataset_id = %s
                   AND batch_key = %s AND checksum = %s AND parser_version = %s""",
                batch_key,
            ).one()
            return {"status": result.status, "reused": True, **result.counts_jsonb}

        issue_errors = [f"{issue.locator}: {issue.message}" for issue in issues]
        if official_manifest is not None:
            insert_artifact(
                conn, batch_id, args.manifest_url, official_manifest, "parsed"
            )
        index_id = insert_artifact(
            conn,
            batch_id,
            args.index_source_url or "index.xml",
            index_raw,
            "quarantined" if index_error else "partial" if issues else "parsed",
            "\n".join(filter(None, [index_error, *issue_errors])) or None,
        )
        metadata = fulltext = quarantined_specs = 0
        pending_specs = specs_raw.copy()
        for record in records:
            spec = spec_id = None
            if artifact := pending_specs.pop(record.publication_no, None):
                error_log = None
                try:
                    sections, claims = parse_specification(
                        store.read(artifact),
                        record.application_no,
                        grant=bool(args.grant_number),
                    )
                    spec = Specification(artifact, sections, claims)
                except (ValueError, ET.ParseError) as error:
                    error_log = str(error)
                    quarantined_specs += 1
                spec_id = insert_artifact(
                    conn,
                    batch_id,
                    sources.get(
                        record.publication_no, f"spec/{record.publication_no}.xml"
                    ),
                    artifact,
                    "parsed" if spec else "quarantined",
                    error_log,
                )
            stage = "grant" if args.grant_number else "publication"
            if spec is None and grant_claims.get(record.publication_no):
                spec = Specification(index_raw, [], grant_claims[record.publication_no])
            document_id = store_document(conn, record, jurisdiction, spec, stage=stage)
            link_artifact(conn, document_id, index_id, record.locator)
            if spec is None:
                metadata += 1
            elif spec.sections:
                locator = (
                    "/specification"
                    if args.grant_number
                    else "/invention-specification"
                )
                link_artifact(conn, document_id, spec_id, locator)
                fulltext += 1

        for number, artifact in pending_specs.items():
            insert_artifact(
                conn,
                batch_id,
                f"spec/{number}.xml",
                artifact,
                "quarantined",
                "No matching publication in selected index range",
            )
            quarantined_specs += 1

        status = (
            "failed"
            if index_error
            else (
                "partial"
                if issues or metadata or quarantined_specs or failures
                else "complete"
            )
        )
        counts = {
            "metadata": metadata,
            "fulltext": fulltext,
            "invalid_records": len(issues),
            "quarantined_specs": quarantined_specs,
        }
        if official_manifest is not None:
            counts["download_failures"] = [
                {
                    "publication_no": number,
                    "source_url": sources[number],
                    "error": error,
                }
                for number, error in failures.items()
            ]
        if args.grant_number:
            counts["grants_with_claims"] = sum(
                bool(claims) for claims in grant_claims.values()
            )
        if records and not args.demo:
            counts["legal_events_linked"] = link_events(
                conn, applications=sorted({record.application_no for record in records})
            )
        conn.exec_driver_sql(
            """UPDATE ingestion_batches SET status = %s, counts_jsonb = %s, finished_at = now()
               WHERE id = %s""",
            (status, Jsonb(counts), batch_id),
        )
        return {"status": status, "reused": False, **counts}


def parse_import_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--index-source-url", help="Official URL of the supplied index")
    parser.add_argument(
        "--batch", required=True, help="Official issue ID or DEMO batch ID"
    )
    add_objects_argument(parser)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument(
        "--grant-number",
        action="append",
        default=[],
        help="Select an invention, utility model or design grant from an official S01 index (repeatable)",
    )
    parser.add_argument("--manifest", type=Path, help="Official index_all.xml file")
    parser.add_argument("--manifest-url", help="Official FTPS URL of the manifest file")
    parser.add_argument(
        "--fetch-only",
        action="store_true",
        help="Fill the download cache without using PostgreSQL",
    )
    parser.add_argument(
        "--cache-only", action="store_true", help="Import without contacting TIPO"
    )
    parser.add_argument(
        "--spec", action="append", default=[], metavar="PUBLICATION=PATH"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--demo", action="store_true")
    mode.add_argument(
        "--verified-tipo",
        action="store_true",
        help="Confirm official artifact provenance",
    )
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= 500:
        parser.error("--limit must be between 1 and 500")
    if len(args.grant_number) > args.limit:
        parser.error("The number of selected grants exceeds --limit")
    if args.index_source_url:
        if args.demo:
            parser.error("--index-source-url requires --verified-tipo")
        try:
            validate_index_source(
                args.index_source_url, args.batch, grant=bool(args.grant_number)
            )
        except ValueError as error:
            parser.error(str(error))
    if bool(args.manifest) != bool(args.manifest_url) or (
        args.manifest and (args.demo or args.spec)
    ):
        parser.error(
            "--manifest and --manifest-url require --verified-tipo and no --spec"
        )
    if (args.fetch_only or args.cache_only) and not args.manifest:
        parser.error("--fetch-only and --cache-only require --manifest")
    if args.fetch_only and args.cache_only:
        parser.error("--fetch-only and --cache-only cannot be combined")
    if args.grant_number and (args.demo or args.spec):
        parser.error(
            "--grant-number requires --verified-tipo and an official manifest for specifications"
        )
    if any(number.startswith(("D", "M")) for number in args.grant_number):
        if args.manifest:
            parser.error(
                "Utility model and design grant imports currently use the S01 index only"
            )
        if not args.index_source_url:
            parser.error("Utility model and design grants require --index-source-url")
    args.specs = {}
    for item in args.spec:
        number, separator, path = item.partition("=")
        if (
            not separator
            or len(number) != 9
            or not number.isascii()
            or not number.isdecimal()
            or not path
        ):
            parser.error(
                "--spec must be PUBLICATION=PATH with a 9-digit publication number"
            )
        if number in args.specs:
            parser.error("Duplicate publication in --spec")
        args.specs[number] = Path(path)
    return args


def main():
    args = parse_import_args()
    result = import_issue(args)
    print(json.dumps(result, ensure_ascii=False))
    return int(
        result["status"] == "failed"
        or (args.fetch_only and result["status"] != "complete")
    )


if __name__ == "__main__":
    raise SystemExit(main())
