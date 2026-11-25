"""Verify a uniquely selected fulltext publication against its archived XML."""

import argparse
from pathlib import Path

from services.api.db import engine
from services.ingestion.artifacts import (
    LocalObjectStore,
    RawArtifact,
    add_objects_argument,
)
from services.ingestion.grant_index import parse_grant
from services.ingestion.specification import parse_specification


def verify(
    publication_no: str, root: Path, grant_issue: str | None = None
) -> tuple[int, int]:
    stage = "grant" if grant_issue else "publication"
    with engine.connect() as conn:
        document_id, application_no, checksum, key, size = conn.exec_driver_sql(
            """SELECT DISTINCT d.id, p.application_no, a.checksum, a.object_key, a.size_bytes
               FROM patent_documents d
               JOIN patent_applications p ON p.id = d.application_id
               JOIN document_artifacts da ON da.document_id = d.id
               JOIN ingestion_artifacts a ON a.id = da.artifact_id
               WHERE d.jurisdiction = 'TW' AND d.document_stage = %s
                 AND d.publication_no = %s
                 AND (da.record_locator = '/invention-specification'
                      OR (d.document_stage = 'grant' AND
                          right(da.record_locator, 1) = ']' AND
                          starts_with(da.record_locator, '/tw-patent-grants/tw-patent-grant[')))""",
            (stage, publication_no),
        ).one()
        payload = LocalObjectStore(root).read(RawArtifact(checksum, key, size))
        if grant_issue:
            grant, claims = parse_grant(payload, grant_issue, publication_no)
            if grant.application_no != application_no:
                raise ValueError(
                    "Archived grant application number differs from the database"
                )
            sections = []
        else:
            sections, claims = parse_specification(payload, application_no)
        stored_claims = (
            conn.exec_driver_sql(
                """SELECT claim_number, text, independent_flag_nullable,
                      source_locator_jsonb->>'xpath', source_locator_jsonb->>'artifact_sha256'
               FROM patent_claims WHERE document_id = %s ORDER BY claim_number""",
                (document_id,),
            )
            .tuples()
            .all()
        )
        stored_sections = (
            conn.exec_driver_sql(
                """SELECT section_type, ordinal, original_text,
                      source_locator_jsonb->>'xpath', source_locator_jsonb->>'artifact_sha256'
               FROM patent_sections WHERE document_id = %s""",
                (document_id,),
            )
            .tuples()
            .all()
        )
    expected_claims = [
        (claim.number, claim.text, claim.independent, claim.locator, checksum)
        for claim in sorted(claims, key=lambda item: item.number)
    ]
    expected_sections = [
        (section.kind, section.ordinal, section.text, section.locator, checksum)
        for section in sections
    ]
    if stored_claims != expected_claims or sorted(stored_sections) != sorted(
        expected_sections
    ):
        raise ValueError(
            "Stored text or source locator differs from the verified raw XML"
        )
    return len(claims), len(sections)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("publication_no")
    add_objects_argument(parser)
    parser.add_argument("--grant-issue")
    args = parser.parse_args()
    claims, sections = verify(args.publication_no, args.objects, args.grant_issue)
    print(
        f"Verified {claims} claims and {sections} description paragraphs against archived XML"
    )
