"""Link verified TIPO event records to known applications."""

from uuid import UUID

from sqlalchemy.engine import Connection

MATCH_LOCK = 920503


def link_events(
    conn: Connection,
    *,
    artifact_id: UUID | None = None,
    applications: list[str] | None = None,
) -> int:
    if artifact_id is None and not applications:
        return 0

    # Serialize matching after either side has written its rows. The second
    # transaction then sees the first commit, regardless of import order.
    conn.exec_driver_sql("SELECT pg_advisory_xact_lock(%s)", (MATCH_LOCK,))
    return conn.exec_driver_sql(
        """INSERT INTO patent_legal_events
               (application_id,artifact_id,kind,certificate_no,effective_on,detail,record_locator)
           SELECT a.id,p.artifact_id,p.kind,p.certificate_no,p.effective_on,p.detail,p.record_locator
           FROM legal_event_catalog p
           JOIN patent_applications a ON a.jurisdiction = 'TW' AND a.application_no = p.application_no
           WHERE (%s::uuid IS NULL OR p.artifact_id = %s)
             AND (%s::text[] IS NULL OR p.application_no = ANY(%s::text[]))
             AND (starts_with(p.certificate_no, 'I') OR EXISTS (
               SELECT 1 FROM patent_documents d WHERE d.application_id = a.id
                 AND d.document_stage = 'grant' AND d.publication_no = p.certificate_no
             ))
             AND NOT EXISTS (
               SELECT 1 FROM patent_documents d WHERE d.application_id = a.id
                 AND d.document_stage = 'grant' AND d.publication_no <> p.certificate_no
             )
           ON CONFLICT (artifact_id,record_locator) DO NOTHING""",
        (artifact_id, artifact_id, applications, applications),
    ).rowcount
