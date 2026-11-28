"""Preserve explicit claim references within individual document versions."""

from itertools import groupby
from operator import itemgetter

from alembic import op
from sqlalchemy import text

from services.ingestion.claim_references_v1 import INSERT_REFERENCES, reference_pairs

revision = "0011_claim_dependencies"
down_revision = "0010_login_failures"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE claim_dependencies (
            document_id uuid NOT NULL,
            child_number integer NOT NULL,
            parent_number integer NOT NULL,
            PRIMARY KEY (document_id, child_number, parent_number),
            CHECK (parent_number < child_number),
            FOREIGN KEY (document_id, child_number)
                REFERENCES patent_claims (document_id, claim_number) ON DELETE CASCADE,
            FOREIGN KEY (document_id, parent_number)
                REFERENCES patent_claims (document_id, claim_number) ON DELETE CASCADE
        )
    """)
    op.create_index(
        "ix_claim_dependencies_parent",
        "claim_dependencies",
        ["document_id", "parent_number"],
    )
    conn = op.get_bind()
    with conn.execute(
        text("""SELECT document_id, claim_number, text
                FROM patent_claims ORDER BY document_id, claim_number"""),
        execution_options={"stream_results": True},
    ) as rows:
        for document_id, claims in groupby(rows, key=itemgetter(0)):
            pairs = reference_pairs((number, text) for _, number, text in claims)
            if pairs:
                conn.exec_driver_sql(
                    INSERT_REFERENCES,
                    [(document_id, child, parent) for child, parent in pairs],
                )


def downgrade():
    op.drop_table("claim_dependencies")
