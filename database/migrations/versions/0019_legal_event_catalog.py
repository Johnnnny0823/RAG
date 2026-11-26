"""Retain verified event records before their patent applications exist."""

from alembic import op

revision = "0019_legal_event_catalog"
down_revision = "0018_audit_logs"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE legal_event_catalog (
            artifact_id uuid NOT NULL REFERENCES ingestion_artifacts(id),
            record_locator text NOT NULL,
            application_no text NOT NULL CHECK (application_no ~ '^[0-9]{9}$'),
            certificate_no text NOT NULL CHECK (certificate_no ~ '^I[0-9]+$'),
            kind text NOT NULL CHECK (kind IN ('extinguishment', 'gazette_correction')),
            effective_on date,
            detail text,
            PRIMARY KEY (artifact_id, record_locator),
            CHECK ((kind = 'extinguishment') = (effective_on IS NOT NULL))
        )
    """)
    op.create_index(
        "ix_legal_event_catalog_application", "legal_event_catalog", ["application_no"]
    )
    op.execute("""
        INSERT INTO legal_event_catalog
            (artifact_id, record_locator, application_no, certificate_no, kind, effective_on, detail)
        SELECT e.artifact_id, e.record_locator, a.application_no, e.certificate_no,
               e.kind, e.effective_on, e.detail
        FROM patent_legal_events e JOIN patent_applications a ON a.id = e.application_id
        WHERE a.jurisdiction = 'TW'
    """)
    # A previous downgrade may have dropped staged events. Rebuild their index
    # from retained originals even when that deployment had marked them complete.
    op.execute("""
        UPDATE ingestion_batches b
        SET counts_jsonb = b.counts_jsonb - 'cataloged_events'
        FROM source_datasets s
        WHERE b.dataset_id = s.id AND s.dataset_key = 'TIPO-15974'
          AND b.counts_jsonb ? 'cataloged_events'
    """)


def downgrade():
    op.drop_table("legal_event_catalog")
