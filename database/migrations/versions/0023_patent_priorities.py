"""Store source-backed priorities for individual patent document versions."""

import sqlalchemy as sa
from alembic import op

revision = "0023_patent_priorities"
down_revision = "0022_legal_event_grant_types"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE patent_priorities (
            document_id uuid NOT NULL,
            artifact_id uuid NOT NULL,
            record_locator text NOT NULL,
            ordinal integer NOT NULL CHECK (ordinal > 0),
            country text NOT NULL CHECK (btrim(country) <> ''),
            priority_no text NOT NULL CHECK (btrim(priority_no) <> ''),
            priority_date date NOT NULL,
            PRIMARY KEY (document_id, country, priority_no, priority_date),
            FOREIGN KEY (document_id, artifact_id, record_locator)
                REFERENCES document_artifacts (document_id, artifact_id, record_locator)
        )
    """)


def downgrade():
    if (
        op.get_bind()
        .execute(sa.text("SELECT EXISTS (SELECT 1 FROM patent_priorities)"))
        .scalar_one()
    ):
        raise RuntimeError("Downgrade would discard indexed patent priorities")
    op.drop_table("patent_priorities")
