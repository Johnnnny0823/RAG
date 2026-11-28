"""Record selected sourced TIPO gazette events by application."""

from alembic import op

revision = "0015_legal_events"
down_revision = "0014_ingestion_jobs"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE patent_legal_events (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            application_id uuid NOT NULL REFERENCES patent_applications(id),
            artifact_id uuid NOT NULL REFERENCES ingestion_artifacts(id),
            kind text NOT NULL CHECK (kind IN ('extinguishment', 'gazette_correction')),
            certificate_no text NOT NULL CHECK (certificate_no ~ '^I[0-9]+$'),
            effective_on date,
            detail text,
            record_locator text NOT NULL,
            UNIQUE (artifact_id, record_locator),
            CHECK ((kind = 'extinguishment') = (effective_on IS NOT NULL))
        )
    """)
    op.create_index(
        "ix_patent_legal_events_application", "patent_legal_events", ["application_id"]
    )


def downgrade():
    op.drop_table("patent_legal_events")
