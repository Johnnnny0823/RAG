"""Import selected invention events from a verified TIPO gazette issue."""

import argparse
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import date

from psycopg.types.json import Jsonb

from services.api.db import engine
from services.ingestion.artifacts import LocalObjectStore, add_objects_argument
from services.ingestion.download import download_ftps_xml
from services.ingestion.gazette_dates import roc_date
from services.ingestion.import_issue import LICENSE_URL
from services.ingestion.patentpub import parse_xml, patent_number

DATASET_URL = "https://data.gov.tw/dataset/15974"
PARSER_VERSION = "tipo-sundry-events-1"
TYPES = {"sud08": "extinguishment", "sud24": "gazette_correction"}


@dataclass(frozen=True)
class LegalEvent:
    application_no: str
    certificate_no: str
    effective_on: date | None
    detail: str | None
    record_locator: str


def archive_url(year: str, issue: str, event_type: str) -> str:
    if (
        not re.fullmatch(r"[0-9]{3}", year)
        or not re.fullmatch(r"[0-9]{6}", issue)
        or event_type not in TYPES
    ):
        raise ValueError(
            "Expected a ROC year, six-digit issue, and supported event type"
        )
    return f"ftps://ftp.tipo.gov.tw/PatentIsuModXML/{year}/PatentIsuModXML_{issue}/{event_type}.xml"


def parse_events(data: bytes, issue: str, event_type: str) -> list[LegalEvent]:
    if event_type not in TYPES:
        raise ValueError("Unsupported gazette event type")
    dataset = event_type.capitalize() + "Dataset"
    namespace = "{http://tempuri.org/" + dataset + ".xsd}"
    doctype = f'<!DOCTYPE {dataset} SYSTEM "{event_type}.dtd"[]>'.encode()
    # Strip only the exact inert external DTD. parse_xml rejects any other DOCTYPE.
    root = parse_xml(data.replace(doctype, b"", 1))
    if root.tag != namespace + dataset or not len(root):
        raise ValueError("Unexpected TIPO event dataset")
    extinct = event_type == "sud08"
    events = []
    for index, item in enumerate(root, 1):
        if item.tag != namespace + event_type:
            raise ValueError("Unexpected TIPO event element")
        volume, number = (
            item.findtext(namespace + tag, "").strip() for tag in ("volno", "isuno")
        )
        if volume.zfill(3) + number.zfill(3) != issue:
            raise ValueError("Event belongs to a different gazette issue")
        certificate_field = "cerno" if extinct else "orgpatno"
        certificate = item.findtext(namespace + certificate_field, "").strip()
        if not re.fullmatch(r"I[0-9]+", certificate):
            continue
        application = patent_number(
            item, namespace + ("aplno" if extinct else "orgaplno")
        )
        effective = (
            roc_date(item.findtext(namespace + "extdt", "").strip())
            if extinct
            else None
        )
        detail = item.findtext(
            namespace + ("extson" if extinct else "fixfld"), ""
        ).strip()
        locator = (
            f"/*[local-name()='{dataset}']/*[local-name()='{event_type}'][{index}]"
        )
        events.append(
            LegalEvent(application, certificate, effective, detail or None, locator)
        )
    return events


def import_events(
    data: bytes, store: LocalObjectStore, year: str, issue: str, event_type: str
) -> dict:
    url = archive_url(year, issue, event_type)
    events = parse_events(data, issue, event_type)
    raw = store.put(data)
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """INSERT INTO source_datasets
                   (dataset_key, name, publisher, official_url, license_notes, checked_at, is_demo)
               VALUES ('TIPO-15974','專利權異動公報(1卷期1異動1XML檔)','經濟部智慧財產局',
                       %s,%s,current_timestamp,false)
               ON CONFLICT (dataset_key) DO NOTHING""",
            (DATASET_URL, LICENSE_URL),
        )
        batch_id = conn.exec_driver_sql(
            """INSERT INTO ingestion_batches
                   (dataset_id,batch_key,checksum,parser_version,status,finished_at)
               SELECT id,%s,%s,%s,'complete',current_timestamp FROM source_datasets
               WHERE dataset_key = 'TIPO-15974'
               ON CONFLICT (dataset_id,batch_key,checksum,parser_version) DO UPDATE
               SET status = 'complete'
               RETURNING id""",
            (issue, raw.checksum, PARSER_VERSION),
        ).scalar_one()
        artifact_id = conn.exec_driver_sql(
            """INSERT INTO ingestion_artifacts
                   (batch_id,source_locator,checksum,object_key,size_bytes,status)
               VALUES (%s,%s,%s,%s,%s,'parsed')
               ON CONFLICT (batch_id,source_locator) DO UPDATE SET status = 'parsed'
               RETURNING id""",
            (batch_id, url, raw.checksum, raw.object_key, raw.size_bytes),
        ).scalar_one()
        inserted = conn.exec_driver_sql(
            """INSERT INTO patent_legal_events
                   (application_id,artifact_id,kind,certificate_no,effective_on,detail,record_locator)
               SELECT a.id,%s,%s,p.certificate_no,p.effective_on,p.detail,p.record_locator
               FROM jsonb_to_recordset(%s) AS p(application_no text, certificate_no text,
                   effective_on date, detail text, record_locator text)
               JOIN patent_applications a ON a.jurisdiction = 'TW' AND a.application_no = p.application_no
               WHERE NOT EXISTS (
                   SELECT 1 FROM patent_documents d WHERE d.application_id = a.id
                     AND d.document_stage = 'grant' AND d.publication_no <> p.certificate_no
               )
               ON CONFLICT (artifact_id,record_locator) DO NOTHING""",
            (
                artifact_id,
                TYPES[event_type],
                Jsonb(
                    [asdict(event) for event in events],
                    dumps=lambda payload: json.dumps(payload, default=date.isoformat),
                ),
            ),
        ).rowcount
        matched = conn.exec_driver_sql(
            "SELECT count(*) FROM patent_legal_events WHERE artifact_id=%s",
            (artifact_id,),
        ).scalar_one()
        counts = {"invention_events": len(events), "matched_events": matched}
        conn.exec_driver_sql(
            "UPDATE ingestion_batches SET counts_jsonb=%s WHERE id=%s",
            (Jsonb(counts), batch_id),
        )
    return {**counts, "new_events": inserted, "sha256": raw.checksum}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", required=True)
    parser.add_argument("--issue", required=True)
    parser.add_argument("--type", choices=TYPES, required=True)
    add_objects_argument(parser)
    args = parser.parse_args()
    try:
        url = archive_url(args.year, args.issue, args.type)
        result = import_events(
            download_ftps_xml(url),
            LocalObjectStore(args.objects),
            args.year,
            args.issue,
            args.type,
        )
    except (OSError, ValueError, ET.ParseError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
