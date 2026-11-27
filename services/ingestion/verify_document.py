"""Verify a uniquely selected document version against its archived XML."""

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
    publication_no: str,
    root: Path,
    grant_issue: str | None = None,
    *,
    grant_fulltext: bool = False,
) -> tuple[int, int]:
    stage = "grant" if grant_issue else "publication"
    index_grant = bool(grant_issue and not grant_fulltext)
    scope = "fulltext"
    if index_grant:
        scope = (
            "metadata_and_abstract" if publication_no.startswith("D") else "claims_only"
        )
    with engine.connect() as conn:
        document_id, application_no, checksum, key, size, source_hash = (
            conn.exec_driver_sql(
                """SELECT DISTINCT d.id, p.application_no, a.checksum, a.object_key,
                               a.size_bytes, d.source_hash
               FROM patent_documents d
               JOIN patent_applications p ON p.id = d.application_id
               JOIN document_artifacts da ON da.document_id = d.id
               JOIN ingestion_artifacts a ON a.id = da.artifact_id
               WHERE d.jurisdiction = 'TW' AND d.document_stage = %s
                 AND d.publication_no = %s
                 AND d.metadata_jsonb->>'content_scope' = %s
                 AND (da.record_locator IN ('/invention-specification','/specification')
                      OR (%s AND
                          right(da.record_locator, 1) = ']' AND
                          starts_with(da.record_locator, '/tw-patent-grants/tw-patent-grant[')))""",
                (stage, publication_no, scope, index_grant),
            ).one()
        )
        payload = LocalObjectStore(root).read(RawArtifact(checksum, key, size))
        if grant_issue and index_grant:
            grant, claims = parse_grant(payload, grant_issue, publication_no)
            if (
                grant.application_no != application_no
                or grant.source_hash != source_hash
            ):
                raise ValueError(
                    "Archived grant application number or source hash differs from the database"
                )
            sections = []
        else:
            sections, claims = parse_specification(
                payload,
                application_no,
                grant_number=publication_no if grant_fulltext else None,
            )
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
    parser.add_argument("--grant-fulltext", action="store_true")
    args = parser.parse_args()
    if args.grant_fulltext and not args.grant_issue:
        parser.error("--grant-fulltext requires --grant-issue")
    claims, sections = verify(
        args.publication_no,
        args.objects,
        args.grant_issue,
        grant_fulltext=args.grant_fulltext,
    )
    print(
        f"Verified document against archived XML: {claims} claims and {sections} description paragraphs"
    )
