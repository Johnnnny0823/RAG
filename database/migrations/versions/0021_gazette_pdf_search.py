"""Index verified PDF page text for bilingual lexical search."""

from alembic import op
from sqlalchemy import text

from services.retrieval.lexical import tokenize

revision = "0021_gazette_pdf_search"
down_revision = "0020_gazette_pdf_pages"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE gazette_pdf_pages ADD COLUMN search_tokens text NOT NULL DEFAULT '',
            ADD COLUMN search_terms tsvector GENERATED ALWAYS AS
                (to_tsvector('simple'::regconfig, search_tokens)) STORED
    """)
    connection = op.get_bind()
    with connection.execute(
        text("SELECT artifact_id, page_number, extracted_text FROM gazette_pdf_pages"),
        execution_options={"stream_results": True},
    ) as rows:
        for batch in rows.partitions(100):
            connection.exec_driver_sql(
                "UPDATE gazette_pdf_pages SET search_tokens=%s WHERE artifact_id=%s AND page_number=%s",
                [
                    (" ".join(tokenize(body)), artifact, page)
                    for artifact, page, body in batch
                ],
            )
    op.execute(
        "CREATE INDEX ix_gazette_pdf_terms ON gazette_pdf_pages USING GIN (search_terms)"
    )


def downgrade():
    op.drop_index("ix_gazette_pdf_terms", table_name="gazette_pdf_pages")
    op.drop_column("gazette_pdf_pages", "search_terms")
    op.drop_column("gazette_pdf_pages", "search_tokens")
