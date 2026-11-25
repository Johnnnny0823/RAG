"""Fill missing dates on indexed versions from the official TIPO gazette XML."""

import argparse
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date

from psycopg.types.json import Jsonb

from services.api.db import engine
from services.ingestion.artifacts import (
    MAX_GAZETTE_XML_BYTES,
    LocalObjectStore,
    add_objects_argument,
)
from services.ingestion.download import download_ftps_xml
from services.ingestion.import_issue import LICENSE_URL, link_artifact
from services.ingestion.patentpub import SafeTreeBuilder, patent_number

PARSER_VERSION = "tipo-gazette-dates-1"
DATASETS = {
    "publication": (
        "9683",
        "發明公開公報書目(1卷期1XML檔)",
        "PatentPubRegXMLB",
        "pubinvention",
        "15996",
    ),
    "grant": (
        "15972",
        "專利公告公報書目(1卷期1XML檔)",
        "PatentIsuRegSpecXMLB",
        "patent",
        "15987",
    ),
}


@dataclass(frozen=True)
class GazetteDates:
    application_no: str
    publication_no: str
    filing_date: date
    publication_date: date
    locator: str


def archive_url(stage: str, year: str, issue: str) -> str:
    if not re.fullmatch(r"[0-9]{3}", year) or not re.fullmatch(r"[0-9]{6}", issue):
        raise ValueError("Expected a three-digit ROC year and six-digit issue")
    _, _, folder, filename, _ = DATASETS[stage]
    return f"ftps://ftp.tipo.gov.tw/{folder}/{year}/{folder}_{issue}/{filename}.xml"


def roc_date(value: str) -> date:
    if not re.fullmatch(r"[0-9]{2,3}/[0-9]{2}/[0-9]{2}", value):
        raise ValueError("Expected a ROC calendar date")
    year, month, day = map(int, value.split("/"))
    if not year:
        raise ValueError("Invalid ROC year")
    return date(year + 1911, month, day)


def parse_gazette(
    data: bytes, stage: str, year: str, issue: str
) -> dict[str, GazetteDates]:
    if not 0 < len(data) <= MAX_GAZETTE_XML_BYTES:
        raise ValueError("Gazette XML exceeds its size limit or is empty")
    record_tag, bibliography_tag, application_type = (
        (
            "tw-patent-application",
            "tw-bibliographic-data-application",
            "invention-public",
        )
        if stage == "publication"
        else ("tw-patent-grant", "tw-bibliographic-data-grant", "invention")
    )
    root = ET.fromstring(data, parser=ET.XMLParser(target=SafeTreeBuilder()))
    if root.tag != record_tag + "s" or root.get("total-count") != str(len(root)):
        raise ValueError("Expected a complete TIPO gazette with the requested stage")
    records = {}
    for ordinal, item in enumerate(root, 1):
        bibliography = item.find(bibliography_tag)
        if item.tag != record_tag or bibliography is None:
            raise ValueError("Unexpected gazette record")
        volume, number = (
            bibliography.findtext(tag, "").strip() for tag in ("volno", "isuno")
        )
        if volume.zfill(3) + number.zfill(3) != issue:
            raise ValueError("Gazette record belongs to a different issue")
        reference = bibliography.find("application-reference")
        if reference is None:
            raise ValueError("Missing gazette application reference")
        if stage == "grant" and reference.get("appl-type") != application_type:
            continue
        if reference.get("appl-type") != application_type:
            raise ValueError("Unexpected gazette application type")
        application_no = patent_number(reference, "document-id/doc-number")
        publication_no = bibliography.findtext(
            "publication-reference/document-id/doc-number", ""
        ).strip()
        number_pattern = r"[0-9]{9}" if stage == "publication" else r"I[0-9]+"
        if not re.fullmatch(number_pattern, publication_no):
            raise ValueError("Invalid gazette document number")
        if stage == "grant" and publication_no != bibliography.findtext(
            "certificate-number/document-id/doc-number"
        ):
            raise ValueError("Gazette announcement and certificate numbers disagree")
        if publication_no in records:
            raise ValueError("Duplicate gazette document number")
        publication_date = roc_date(
            bibliography.findtext("publication-reference/document-id/date", "").strip()
        )
        filing_date = roc_date(reference.findtext("document-id/date", "").strip())
        if publication_date.year != int(year) + 1911 or filing_date > publication_date:
            raise ValueError("Gazette record dates disagree with the archive")
        records[publication_no] = GazetteDates(
            application_no,
            publication_no,
            filing_date,
            publication_date,
            f"/{root.tag}/{record_tag}[{ordinal}]/{bibliography_tag}",
        )
    if not records:
        raise ValueError("Gazette contains no invention dates")
    return records


def apply_dates(
    data: bytes, store: LocalObjectStore, stage: str, year: str, issue: str
) -> dict:
    url = archive_url(stage, year, issue)
    records = parse_gazette(data, stage, year, issue)
    raw = store.put(data)
    catalog, dataset_name, _, _, original_catalog = DATASETS[stage]
    with engine.begin() as conn:
        documents = conn.exec_driver_sql(
            """SELECT d.id, d.application_id, d.publication_no, a.application_no
               FROM patent_documents d JOIN patent_applications a ON a.id = d.application_id
               WHERE d.jurisdiction = 'TW' AND a.jurisdiction = 'TW' AND d.document_stage = %s
                 AND EXISTS (
                    SELECT 1 FROM document_artifacts da
                    JOIN ingestion_artifacts ia ON ia.id = da.artifact_id
                    JOIN ingestion_batches b ON b.id = ia.batch_id
                    JOIN source_datasets s ON s.id = b.dataset_id
                    WHERE da.document_id = d.id AND b.batch_key = %s AND s.dataset_key = %s
                      AND NOT s.is_demo AND b.status IN ('complete', 'partial')
                      AND ia.status IN ('parsed', 'partial')
                 )
               ORDER BY d.application_id, d.id""",
            (stage, issue, f"TIPO-{original_catalog}"),
        ).all()
        if not documents:
            raise ValueError(
                "No existing official versions in the requested stage and issue"
            )
        for document in documents:
            record = records.get(document.publication_no)
            if record is None or record.application_no != document.application_no:
                raise ValueError(
                    f"Gazette identity mismatch for {document.publication_no}"
                )

        dataset_id = conn.exec_driver_sql(
            """INSERT INTO source_datasets
                   (dataset_key, name, publisher, official_url, license_notes, checked_at, is_demo)
               VALUES (%s,%s,'經濟部智慧財產局',%s,%s,current_timestamp,false)
               ON CONFLICT (dataset_key) DO UPDATE SET checked_at = current_timestamp
               RETURNING id""",
            (
                f"TIPO-{catalog}",
                dataset_name,
                f"https://data.gov.tw/dataset/{catalog}",
                LICENSE_URL,
            ),
        ).scalar_one()
        counts = {
            "matched_versions": len(documents),
            "gazette_inventions": len(records),
        }
        batch_id = conn.exec_driver_sql(
            """INSERT INTO ingestion_batches
                   (dataset_id, batch_key, checksum, parser_version, status, counts_jsonb, finished_at)
               VALUES (%s,%s,%s,%s,'complete',%s,current_timestamp)
               ON CONFLICT (dataset_id, batch_key, checksum, parser_version) DO UPDATE
                   SET counts_jsonb = excluded.counts_jsonb
               RETURNING id""",
            (dataset_id, issue, raw.checksum, PARSER_VERSION, Jsonb(counts)),
        ).scalar_one()
        artifact_id = conn.exec_driver_sql(
            """INSERT INTO ingestion_artifacts
                   (batch_id, source_locator, checksum, object_key, size_bytes, status)
               VALUES (%s,%s,%s,%s,%s,'parsed')
               ON CONFLICT (batch_id, source_locator) DO UPDATE SET status = 'parsed'
               RETURNING id""",
            (batch_id, url, raw.checksum, raw.object_key, raw.size_bytes),
        ).scalar_one()
        for document in documents:
            record = records[document.publication_no]
            application_updated = conn.exec_driver_sql(
                """UPDATE patent_applications SET filing_date = %s
                   WHERE id = %s AND (filing_date IS NULL OR filing_date = %s)""",
                (record.filing_date, document.application_id, record.filing_date),
            ).rowcount
            document_updated = conn.exec_driver_sql(
                """UPDATE patent_documents SET publication_date = %s
                   WHERE id = %s AND (publication_date IS NULL OR publication_date = %s)""",
                (record.publication_date, document.id, record.publication_date),
            ).rowcount
            if application_updated != 1 or document_updated != 1:
                raise ValueError(
                    f"Stored dates disagree with gazette for {record.publication_no}"
                )
            link_artifact(conn, document.id, artifact_id, record.locator)
    return {**counts, "sha256": raw.checksum}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=DATASETS, required=True)
    parser.add_argument("--year", required=True)
    parser.add_argument("--issue", required=True)
    add_objects_argument(parser)
    args = parser.parse_args()
    try:
        url = archive_url(args.stage, args.year, args.issue)
        result = apply_dates(
            download_ftps_xml(url),
            LocalObjectStore(args.objects),
            args.stage,
            args.year,
            args.issue,
        )
    except (OSError, ValueError, ET.ParseError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
