"""Verify and attach a TIPO invention gazette PDF to its exact document version."""

import argparse
import hashlib
import io
import json
import re
import unicodedata
from dataclasses import dataclass
from http.client import HTTPException, HTTPSConnection
from uuid import UUID

from psycopg.types.json import Jsonb
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from services.api.db import engine
from services.ingestion.artifacts import SHA256, LocalObjectStore, add_objects_argument
from services.ingestion.import_issue import link_artifact
from services.retrieval.lexical import tokenize

HOST = "cloud.tipo.gov.tw"
MAX_PDF_BYTES = 2 * 1024 * 1024
MAX_PAGE_CHARACTERS = 20_000


@dataclass(frozen=True)
class Gazette:
    stage: str
    catalog: str
    case_endpoint: str
    file_directory: str
    number_key: str
    pdf_heading: str
    number_label: str
    xml_dataset: str
    pdf_dataset: str
    pdf_dataset_name: str


PUBLICATION = Gazette(
    stage="publication",
    catalog="invention",
    case_endpoint="laid-opens/cases/pubsud01",
    file_directory="invention/pub",
    number_key="publicationNo",
    pdf_heading="【12】發明公開公報(A)",
    number_label="公開編號",
    xml_dataset="TIPO-15996",
    pdf_dataset="TIPO-INVENTION-GAZETTE-PDF",
    pdf_dataset_name="發明公開公報個案 PDF",
)
GRANT = Gazette(
    stage="grant",
    catalog="patent",
    case_endpoint="grants/cases/sud00_1",
    file_directory="patent/isu",
    number_key="certificateNo",
    pdf_heading="【12】專利公報(B)",
    number_label="證書號數",
    xml_dataset="TIPO-15987",
    pdf_dataset="TIPO-GRANT-GAZETTE-PDF",
    pdf_dataset_name="發明公告公報個案 PDF",
)


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


def checked_pdf_path(
    metadata, application: str, number: str, issue: str, gazette: Gazette = PUBLICATION
) -> str:
    case = metadata.get("patentDoc") if isinstance(metadata, dict) else None
    path = f"/S220/downloads/{gazette.file_directory}{issue}/pdfdata/{application}.pdf"
    if not isinstance(case, dict) or (
        case.get("applicationNo"),
        case.get(gazette.number_key),
        case.get("vol"),
        case.get("no"),
        case.get("pdfUrl"),
    ) != (
        application,
        number,
        int(issue[:3]),
        int(issue[3:]),
        f"https://{HOST}{path}",
    ):
        raise ValueError("TIPO gazette identity or PDF location does not match")
    return path


def verify_pdf(
    data: bytes, application: str, number: str, gazette: Gazette = PUBLICATION
) -> list[str]:
    if len(data) > MAX_PDF_BYTES or not data.startswith(b"%PDF-"):
        raise ValueError("Invalid or oversized gazette PDF")
    reader = PdfReader(io.BytesIO(data), strict=True)
    if reader.is_encrypted or not 1 <= len(reader.pages) <= 32:
        raise ValueError("Unsupported gazette PDF page count or encryption")
    first_page = reader.pages[0].extract_text()
    page = unicodedata.normalize("NFKC", first_page)
    page = re.sub(r"\s+", "", page)
    if not (
        gazette.pdf_heading in page
        and re.search(rf"{gazette.number_label}:{re.escape(number)}(?![0-9])", page)
        and re.search(rf"申請案號:{re.escape(application)}(?![0-9])", page)
    ):
        raise ValueError("Gazette PDF first-page identity does not match")
    pages = [first_page, *(page.extract_text() for page in reader.pages[1:])]
    if any(len(text) > MAX_PAGE_CHARACTERS or "\x00" in text for text in pages):
        raise ValueError("Gazette PDF page text exceeds its limits")
    return pages


def attach_pdf(
    store, data, document_id, application, number, issue, url, pages, gazette
):
    with engine.begin() as conn:
        existing = conn.exec_driver_sql(
            """SELECT d.id FROM patent_documents d
               JOIN patent_applications p ON p.id = d.application_id
               JOIN document_artifacts da ON da.document_id = d.id
               JOIN ingestion_artifacts ia ON ia.id = da.artifact_id
               JOIN ingestion_batches b ON b.id = ia.batch_id
               JOIN source_datasets s ON s.id = b.dataset_id
               WHERE d.id=%s AND d.jurisdiction='TW' AND p.jurisdiction='TW'
                 AND d.document_stage=%s AND d.publication_no=%s
                 AND p.application_no=%s AND b.batch_key=%s AND s.dataset_key=%s
                 AND NOT s.is_demo AND ia.status IN ('parsed', 'partial')
                 AND b.status IN ('complete', 'partial') LIMIT 1""",
            (
                document_id,
                gazette.stage,
                number,
                application,
                issue,
                gazette.xml_dataset,
            ),
        ).scalar_one_or_none()
        if existing is None:
            raise ValueError("No matching official document version in this issue")
        raw = store.put(data)
        dataset_id = conn.exec_driver_sql(
            """INSERT INTO source_datasets
                   (dataset_key, name, publisher, official_url, checked_at, is_demo)
               VALUES (%s, %s, '經濟部智慧財產局', %s, now(), false)
               ON CONFLICT (dataset_key) DO UPDATE SET checked_at=excluded.checked_at
               RETURNING id""",
            (
                gazette.pdf_dataset,
                gazette.pdf_dataset_name,
                f"https://{HOST}/S220/gazette/{gazette.catalog}",
            ),
        ).scalar_one()
        batch_id = conn.exec_driver_sql(
            """INSERT INTO ingestion_batches
                   (dataset_id, batch_key, checksum, parser_version, counts_jsonb, status, finished_at)
               VALUES (%s,%s,%s,%s,%s,'complete',now())
               ON CONFLICT (dataset_id,batch_key,checksum,parser_version) DO UPDATE
                   SET counts_jsonb=excluded.counts_jsonb
               RETURNING id""",
            (
                dataset_id,
                issue,
                raw.checksum,
                f"tipo-{gazette.stage}-gazette-pdf-v1",
                Jsonb({"pages": len(pages)}),
            ),
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
        conn.exec_driver_sql(
            """INSERT INTO gazette_pdf_pages
                   (artifact_id, page_number, extracted_text, search_tokens)
               VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING""",
            [
                (artifact_id, number, text, " ".join(tokenize(text)))
                for number, text in enumerate(pages, 1)
            ],
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--application", required=True)
    number_group = parser.add_mutually_exclusive_group(required=True)
    number_group.add_argument("--publication")
    number_group.add_argument("--grant", help="Invention grant certificate number")
    parser.add_argument("--issue", required=True)
    parser.add_argument(
        "--expected-sha256", help="Require this known official PDF digest"
    )
    parser.add_argument(
        "--apply-to", type=UUID, help="Attach to this existing document version"
    )
    add_objects_argument(parser)
    args = parser.parse_args()
    gazette = GRANT if args.grant is not None else PUBLICATION
    number = args.grant.upper() if gazette is GRANT else args.publication
    pattern = r"I[0-9]{6,}" if gazette is GRANT else r"[0-9]{9}"
    if not (
        re.fullmatch(r"[0-9]{9}", args.application)
        and re.fullmatch(r"[0-9]{6}", args.issue)
        and re.fullmatch(pattern, number)
    ):
        parser.error("Invalid application, document or issue number")
    if args.expected_sha256 is not None and not SHA256.fullmatch(args.expected_sha256):
        parser.error("Expected SHA-256 must be 64 lowercase hexadecimal digits")
    try:
        catalog_path = (
            f"/S220/gazette/api/patents/{gazette.case_endpoint}/{args.application}"
        )
        metadata = json.loads(fetch(catalog_path, "application/json", 1024 * 1024))
        path = checked_pdf_path(metadata, args.application, number, args.issue, gazette)
        data = fetch(path, "application/pdf", MAX_PDF_BYTES)
        checksum = hashlib.sha256(data).hexdigest()
        if args.expected_sha256 and checksum != args.expected_sha256:
            raise ValueError("Gazette PDF does not match its expected SHA-256")
        pages = verify_pdf(data, args.application, number, gazette)
        url = f"https://{HOST}{path}"
        if args.apply_to:
            attach_pdf(
                LocalObjectStore(args.objects),
                data,
                args.apply_to,
                args.application,
                number,
                args.issue,
                url,
                pages,
                gazette,
            )
    except (OSError, ValueError, HTTPException, PyPdfError) as error:
        parser.exit(1, f"{error}\n")
    print(
        json.dumps(
            {
                "source_url": url,
                "sha256": checksum,
                "pages": len(pages),
                "attached": args.apply_to is not None,
            }
        )
    )


if __name__ == "__main__":
    main()
