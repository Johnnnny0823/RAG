"""Preserve extracted page text for verified gazette PDF artifacts."""

from alembic import op

revision = "0020_gazette_pdf_pages"
down_revision = "0019_legal_event_catalog"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE gazette_pdf_pages (
            artifact_id uuid NOT NULL REFERENCES ingestion_artifacts(id),
            page_number integer NOT NULL CHECK (page_number BETWEEN 1 AND 32),
            extracted_text text NOT NULL CHECK (char_length(extracted_text) <= 20000),
            PRIMARY KEY (artifact_id, page_number)
        )
    """)


def downgrade():
    op.drop_table("gazette_pdf_pages")
