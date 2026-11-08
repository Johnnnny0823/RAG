"""Import a bounded sample from a verified TIPO issue index and its XML specs."""

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from psycopg.types.json import Jsonb
from sqlalchemy.engine import Connection

from services.api.db import engine
from services.ingestion.artifacts import MAX_XML_BYTES, LocalObjectStore, RawArtifact
from services.ingestion.issue_index import parse_issue_index
from services.ingestion.patentpub import PatentPublication
from services.ingestion.specification import Claim, Section, parse_specification

PARSER_VERSION = "tipo-issue-1"
DATASET_URL = "https://data.gov.tw/dataset/15996"
LICENSE_URL = "https://data.gov.tw/license"


@dataclass(frozen=True)
class Specification:
    artifact: RawArtifact
    sections: list[Section]
    claims: list[Claim]


def read_xml(path: Path) -> bytes:
    with path.open("rb") as stream:
        payload = stream.read(MAX_XML_BYTES + 1)
    if len(payload) > MAX_XML_BYTES:
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
    if spec is not None:
        source_hash = hashlib.sha256(
            f"{source_hash}:{spec.artifact.checksum}".encode()
        ).hexdigest()
    key = (jurisdiction, record.publication_no, source_hash, PARSER_VERSION)
    document_id = conn.exec_driver_sql(
        """INSERT INTO patent_documents
           (jurisdiction, publication_no, source_hash, parser_version,
            application_id, document_stage, kind_code, publication_date, title_zh, title_en,
            abstract_zh, abstract_en, metadata_jsonb)
           VALUES (%s,%s,%s,%s,%s,'publication','',%s,%s,%s,%s,%s,%s)
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
                    "content_scope": "fulltext" if spec else "metadata_and_abstract",
                }
            ),
        ),
    ).scalar_one_or_none()
    if document_id is None:
        return conn.exec_driver_sql(
            """SELECT id FROM patent_documents WHERE jurisdiction = %s AND publication_no = %s
               AND source_hash = %s AND parser_version = %s
               AND document_stage = 'publication' AND kind_code = ''""",
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
    return document_id


def link_artifact(conn, document_id, artifact_id, locator):
    conn.exec_driver_sql(
        """INSERT INTO document_artifacts (document_id, artifact_id, record_locator)
           VALUES (%s,%s,%s) ON CONFLICT DO NOTHING""",
        (document_id, artifact_id, locator),
    )


def import_issue(args):
    store = LocalObjectStore(args.objects)
    data = read_xml(args.index)
    index_raw = store.put(data)
    specs_raw = {}
    for number, path in args.specs.items():
        payload = read_xml(path)
        specs_raw[number] = (payload, store.put(payload))
    manifest = {
        "index": index_raw.checksum,
        "limit": args.limit,
        "specs": {number: raw.checksum for number, (_, raw) in specs_raw.items()},
    }
    checksum = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    index_error = None
    try:
        records, issues = parse_issue_index(
            data, args.limit, None if args.demo else args.batch
        )
        if not records:
            index_error = "No usable records in selected issue range"
    except (ValueError, ET.ParseError) as error:
        records, issues, index_error = [], [], str(error)

    jurisdiction = "DEMO" if args.demo else "TW"
    dataset_key = "DEMO-issue-index" if args.demo else "TIPO-15996"
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """INSERT INTO source_datasets
               (dataset_key, name, publisher, official_url, license_notes, checked_at, is_demo)
               VALUES (%s,%s,%s,%s,%s,'2026-11-09T00:00:00+08:00',%s)
               ON CONFLICT (dataset_key) DO NOTHING""",
            (
                dataset_key,
                "DEMO fixture" if args.demo else "發明公開說明書(1案1XML檔)",
                "DEMO" if args.demo else "經濟部智慧財產局",
                None if args.demo else DATASET_URL,
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
        index_id = insert_artifact(
            conn,
            batch_id,
            "index.xml",
            index_raw,
            "quarantined" if index_error else "partial" if issues else "parsed",
            "\n".join(filter(None, [index_error, *issue_errors])) or None,
        )
        metadata = fulltext = quarantined_specs = 0
        pending_specs = specs_raw.copy()
        for record in records:
            spec = spec_id = None
            if raw_spec := pending_specs.pop(record.publication_no, None):
                payload, artifact = raw_spec
                error_log = None
                try:
                    sections, claims = parse_specification(
                        payload, record.application_no
                    )
                    spec = Specification(artifact, sections, claims)
                except (ValueError, ET.ParseError) as error:
                    error_log = str(error)
                    quarantined_specs += 1
                spec_id = insert_artifact(
                    conn,
                    batch_id,
                    f"spec/{record.publication_no}.xml",
                    artifact,
                    "parsed" if spec else "quarantined",
                    error_log,
                )
            document_id = store_document(conn, record, jurisdiction, spec)
            link_artifact(conn, document_id, index_id, record.locator)
            if spec is None:
                metadata += 1
            else:
                link_artifact(conn, document_id, spec_id, "/invention-specification")
                fulltext += 1

        for number, (_, artifact) in pending_specs.items():
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
            else ("partial" if issues or metadata or quarantined_specs else "complete")
        )
        counts = {
            "metadata": metadata,
            "fulltext": fulltext,
            "invalid_records": len(issues),
            "quarantined_specs": quarantined_specs,
        }
        conn.exec_driver_sql(
            """UPDATE ingestion_batches SET status = %s, counts_jsonb = %s, finished_at = now()
               WHERE id = %s""",
            (status, Jsonb(counts), batch_id),
        )
        return {"status": status, "reused": False, **counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument(
        "--batch", required=True, help="Official issue ID or DEMO batch ID"
    )
    parser.add_argument("--objects", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=100)
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
    args = parser.parse_args()
    if not 1 <= args.limit <= 500:
        parser.error("--limit must be between 1 and 500")
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
    result = import_issue(args)
    print(json.dumps(result, ensure_ascii=False))
    return int(result["status"] == "failed")


if __name__ == "__main__":
    raise SystemExit(main())
