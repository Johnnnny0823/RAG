"""Attach one official JPEG from an already verified grant specification."""

import argparse
import hashlib
import json
import re
from ftplib import all_errors
from uuid import UUID

from services.api.db import engine
from services.ingestion.artifacts import (
    SHA256,
    LocalObjectStore,
    RawArtifact,
    add_objects_argument,
)
from services.ingestion.download import download_verified_path
from services.ingestion.import_issue import link_artifact
from services.ingestion.patentpub import APPLICATION_NUMBER_PATTERN, parse_xml
from services.ingestion.specification import GRANT_DOCTYPE

HOST = "ftps://ftp.tipo.gov.tw"
DRAWING_DATASET = "TIPO-15987-DRAWINGS"
MAX_DRAWING_BYTES = 2 * 1024 * 1024
DRAWING_LOCATOR = "/specification/drawings/figure[{position}]/img[1]"


def drawing_source(xml_source, xml, number, application, issue, position):
    case_path, _, filename = xml_source.removeprefix(HOST).rpartition("/")
    if (
        not xml_source.startswith(HOST + "/")
        or not re.fullmatch(
            rf"/PatentPubXML/[0-9]{{3}}/PatentPubXML_{issue}/[0-9]+{number}", case_path
        )
        or not re.fullmatch(rf"{application}-[A-Za-z0-9_-]+\.xml", filename)
    ):
        raise ValueError("Unverified TIPO specification path")
    root = parse_xml(xml.replace(GRANT_DOCTYPE, b"", 1))
    figures = root.findall("drawings/figure")
    if (
        root.tag != "specification"
        or root.get("application-num") != application
        or not 1 <= position <= len(figures)
    ):
        raise ValueError("Drawing position or specification identity does not match")
    images = figures[position - 1].findall("img")
    relative = images[0].get("file", "") if len(images) == 1 else ""
    if not re.fullmatch(rf"IMG-2/Draw/{application}-[A-Za-z0-9_-]+\.JPG", relative):
        raise ValueError("Unverified TIPO drawing path")
    return f"{case_path}/{relative}", DRAWING_LOCATOR.format(position=position)


def attach(store, document_id, specification_sha256, position, expected_sha256):
    with engine.connect() as conn:
        verified = conn.exec_driver_sql(
            """SELECT DISTINCT d.publication_no, p.application_no, b.batch_key,
                         ia.source_locator, ia.checksum, ia.object_key, ia.size_bytes
               FROM patent_documents d
               JOIN patent_applications p ON p.id = d.application_id
               JOIN document_artifacts da ON da.document_id = d.id
               JOIN ingestion_artifacts ia ON ia.id = da.artifact_id
               JOIN ingestion_batches b ON b.id = ia.batch_id
               JOIN source_datasets s ON s.id = b.dataset_id
               WHERE d.id=%s AND d.jurisdiction='TW' AND d.document_stage='grant'
                 AND da.record_locator='/specification' AND ia.checksum=%s
                 AND ia.status='parsed' AND b.status IN ('complete','partial')
                 AND s.dataset_key='TIPO-15987' AND NOT s.is_demo""",
            (document_id, specification_sha256),
        ).one_or_none()
    if verified is None:
        raise ValueError("No matching official specification attached to this document")
    number, application, issue, source, digest, key, size = verified
    if not (
        re.fullmatch(r"[IMD][0-9]{1,12}", number)
        and re.fullmatch(
            APPLICATION_NUMBER_PATTERN if number.startswith("D") else r"[0-9]{9}",
            application,
        )
        and re.fullmatch(r"[0-9]{6}", issue)
    ):
        raise ValueError("Invalid official grant identifiers")
    xml = store.read(RawArtifact(digest, key, size))
    path, locator = drawing_source(source, xml, number, application, issue, position)
    url = HOST + path
    result = {"source_url": url, "artifact_sha256": expected_sha256, "xpath": locator}
    with engine.connect() as conn:
        stored = conn.exec_driver_sql(
            """SELECT DISTINCT ia.checksum, ia.object_key, ia.size_bytes
               FROM document_artifacts da
               JOIN ingestion_artifacts ia ON ia.id=da.artifact_id
               JOIN ingestion_batches b ON b.id=ia.batch_id
               JOIN source_datasets s ON s.id=b.dataset_id
               WHERE da.document_id=%s AND da.record_locator=%s
                 AND ia.source_locator=%s AND ia.checksum=%s AND ia.status='parsed'
                 AND b.status='complete' AND s.dataset_key=%s AND NOT s.is_demo""",
            (document_id, locator, url, expected_sha256, DRAWING_DATASET),
        ).one_or_none()
    if stored is not None:
        store.read(RawArtifact(*stored))
        return result
    data = download_verified_path(path, MAX_DRAWING_BYTES)
    if not data.startswith(b"\xff\xd8\xff") or not data.endswith(b"\xff\xd9"):
        raise ValueError("Official drawing is not a JPEG")
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("Official drawing differs from its expected SHA-256")
    image = store.put(data)
    with engine.begin() as conn:
        dataset_id = conn.exec_driver_sql(
            """INSERT INTO source_datasets (dataset_key, name, publisher, official_url, license_notes, checked_at, is_demo)
               SELECT %s, '專利說明書個案圖式', publisher, official_url, license_notes, now(), false
               FROM source_datasets WHERE dataset_key='TIPO-15987' AND NOT is_demo
               ON CONFLICT (dataset_key) DO UPDATE SET checked_at=excluded.checked_at
               RETURNING id""",
            (DRAWING_DATASET,),
        ).scalar_one()
        batch_id = conn.exec_driver_sql(
            """INSERT INTO ingestion_batches (dataset_id, batch_key, checksum, parser_version, status, finished_at)
               VALUES (%s,%s,%s,'tipo-grant-drawing-v1','complete',now())
               ON CONFLICT (dataset_id,batch_key,checksum,parser_version)
               DO UPDATE SET checksum=excluded.checksum RETURNING id""",
            (dataset_id, issue, image.checksum),
        ).scalar_one()
        artifact_id = conn.exec_driver_sql(
            """INSERT INTO ingestion_artifacts (batch_id, source_locator, checksum, object_key, size_bytes, status)
               VALUES (%s,%s,%s,%s,%s,'parsed')
               ON CONFLICT (batch_id,source_locator) DO UPDATE SET status=excluded.status
               WHERE ingestion_artifacts.checksum=excluded.checksum
                 AND ingestion_artifacts.object_key=excluded.object_key
                 AND ingestion_artifacts.size_bytes=excluded.size_bytes
               RETURNING id""",
            (batch_id, url, image.checksum, image.object_key, image.size_bytes),
        ).scalar_one_or_none()
        if artifact_id is None:
            raise ValueError("Existing drawing record differs from the verified JPEG")
        link_artifact(conn, document_id, artifact_id, locator)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply-to", required=True, type=UUID)
    parser.add_argument("--specification-sha256", required=True)
    parser.add_argument(
        "--figure", required=True, type=int, help="One-based XML figure position"
    )
    parser.add_argument("--expected-sha256", required=True)
    add_objects_argument(parser)
    args = parser.parse_args()
    if (
        not SHA256.fullmatch(args.specification_sha256)
        or not SHA256.fullmatch(args.expected_sha256)
        or not 1 <= args.figure <= 1000
    ):
        parser.error(
            "Expected lowercase SHA-256 values and a figure position from 1 to 1000"
        )
    try:
        result = attach(
            LocalObjectStore(args.objects),
            args.apply_to,
            args.specification_sha256,
            args.figure,
            args.expected_sha256,
        )
    except (*all_errors, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
