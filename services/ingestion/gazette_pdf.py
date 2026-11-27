"""Verify and attach a TIPO publication gazette PDF to an existing version."""

import argparse
import hashlib
import io
import json
import re
import unicodedata
from http.client import HTTPException, HTTPSConnection
from uuid import UUID

from psycopg.types.json import Jsonb
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from services.api.db import engine
from services.ingestion.artifacts import LocalObjectStore, add_objects_argument
from services.ingestion.import_issue import link_artifact

HOST = "cloud.tipo.gov.tw"
GAZETTE = f"https://{HOST}/S220/gazette/invention"
PARSER_VERSION = "tipo-publication-gazette-pdf-v1"
MAX_PDF_BYTES = 2 * 1024 * 1024


def fetch(path: str, media_type: str, limit: int) -> bytes:
    conn = HTTPSConnection(HOST, timeout=20)
    try:
        conn.request("GET", path)
        response = conn.getresponse()
        if response.status != 200 or response.headers.get_content_type() != media_type:
            raise ValueError(f"TIPO did not return the expected {media_type}")
        payload = response.read(limit + 1)
        if not payload or len(payload) > limit:
            raise ValueError("TIPO response is empty or exceeds the size limit")
        return payload
    finally:
        conn.close()


def checked_pdf_path(metadata, application: str, publication: str, issue: str) -> str:
    case = metadata.get("patentDoc") if isinstance(metadata, dict) else None
    path = f"/S220/downloads/invention/pub{issue}/pdfdata/{application}.pdf"
    if not isinstance(case, dict) or (
        case.get("applicationNo"),
        case.get("publicationNo"),
        case.get("vol"),
        case.get("no"),
        case.get("pdfUrl"),
    ) != (
        application,
        publication,
        int(issue[:3]),
        int(issue[3:]),
        f"https://{HOST}{path}",
    ):
        raise ValueError("TIPO gazette identity or PDF location does not match")
    return path


def verify_pdf(data: bytes, application: str, publication: str) -> int:
    if len(data) > MAX_PDF_BYTES or not data.startswith(b"%PDF-"):
        raise ValueError("Invalid or oversized gazette PDF")
    reader = PdfReader(io.BytesIO(data), strict=True)
    if reader.is_encrypted or not 1 <= len(reader.pages) <= 32:
        raise ValueError("Unsupported gazette PDF page count or encryption")
    page = unicodedata.normalize("NFKC", reader.pages[0].extract_text())
    page = re.sub(r"\s+", "", page)
    if not (
        re.search(rf"公開編號:{re.escape(publication)}(?![0-9])", page)
        and re.search(rf"申請案號:{re.escape(application)}(?![0-9])", page)
    ):
        raise ValueError("Gazette PDF first-page identity does not match")
    return len(reader.pages)


def attach_pdf(store, data, document_id, application, publication, issue, url, pages):
    with engine.begin() as conn:
        existing = conn.exec_driver_sql(
            """SELECT d.id FROM patent_documents d
               JOIN patent_applications p ON p.id = d.application_id
               JOIN document_artifacts da ON da.document_id = d.id
               JOIN ingestion_artifacts ia ON ia.id = da.artifact_id
               JOIN ingestion_batches b ON b.id = ia.batch_id
               JOIN source_datasets s ON s.id = b.dataset_id
               WHERE d.id=%s AND d.jurisdiction='TW' AND p.jurisdiction='TW'
                 AND d.document_stage='publication' AND d.publication_no=%s
                 AND p.application_no=%s AND b.batch_key=%s AND s.dataset_key='TIPO-15996'
                 AND NOT s.is_demo AND ia.status IN ('parsed', 'partial')
                 AND b.status IN ('complete', 'partial') LIMIT 1""",
            (document_id, publication, application, issue),
        ).scalar_one_or_none()
        if existing is None:
            raise ValueError("No matching official publication version in this issue")
        raw = store.put(data)
        dataset_id = conn.exec_driver_sql(
            """INSERT INTO source_datasets
                   (dataset_key, name, publisher, official_url, checked_at, is_demo)
               VALUES ('TIPO-INVENTION-GAZETTE-PDF', '發明公開公報個案 PDF',
                       '經濟部智慧財產局', %s, now(), false)
               ON CONFLICT (dataset_key) DO UPDATE SET checked_at=excluded.checked_at
               RETURNING id""",
            (GAZETTE,),
        ).scalar_one()
        batch_id = conn.exec_driver_sql(
            """INSERT INTO ingestion_batches
                   (dataset_id, batch_key, checksum, parser_version, counts_jsonb, status, finished_at)
               VALUES (%s,%s,%s,%s,%s,'complete',now())
               ON CONFLICT (dataset_id,batch_key,checksum,parser_version) DO UPDATE
                   SET counts_jsonb=excluded.counts_jsonb
               RETURNING id""",
            (dataset_id, issue, raw.checksum, PARSER_VERSION, Jsonb({"pages": pages})),
        ).scalar_one()
        artifact_id = conn.exec_driver_sql(
            """INSERT INTO ingestion_artifacts
                   (batch_id, source_locator, checksum, object_key, size_bytes, status)
               VALUES (%s,%s,%s,%s,%s,'parsed')
               ON CONFLICT (batch_id, source_locator) DO UPDATE SET status='parsed'
               RETURNING id""",
            (batch_id, url, raw.checksum, raw.object_key, raw.size_bytes),
        ).scalar_one()
        link_artifact(conn, document_id, artifact_id, "PDF page 1")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--application", required=True)
    parser.add_argument("--publication", required=True)
    parser.add_argument("--issue", required=True)
    parser.add_argument(
        "--apply-to", type=UUID, help="Attach to this existing document version"
    )
    add_objects_argument(parser)
    args = parser.parse_args()
    for value, length in (
        (args.application, 9),
        (args.publication, 9),
        (args.issue, 6),
    ):
        if not re.fullmatch(rf"[0-9]{{{length}}}", value):
            parser.error("Invalid application, publication or issue number")
    try:
        catalog_path = (
            f"/S220/gazette/api/patents/laid-opens/cases/pubsud01/{args.application}"
        )
        metadata = json.loads(fetch(catalog_path, "application/json", 1024 * 1024))
        path = checked_pdf_path(
            metadata, args.application, args.publication, args.issue
        )
        data = fetch(path, "application/pdf", MAX_PDF_BYTES)
        pages = verify_pdf(data, args.application, args.publication)
        url = f"https://{HOST}{path}"
        if args.apply_to:
            attach_pdf(
                LocalObjectStore(args.objects),
                data,
                args.apply_to,
                args.application,
                args.publication,
                args.issue,
                url,
                pages,
            )
    except (OSError, ValueError, HTTPException, PyPdfError) as error:
        parser.exit(1, f"{error}\n")
    print(
        json.dumps(
            {
                "source_url": url,
                "sha256": hashlib.sha256(data).hexdigest(),
                "pages": pages,
                "attached": args.apply_to is not None,
            }
        )
    )


if __name__ == "__main__":
    main()
