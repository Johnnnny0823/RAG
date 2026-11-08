"""Add the versioned lexical index for patent text chunks."""

from alembic import op

revision = "0003_lexical"
down_revision = "0002_ingestion"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE patent_lexical_chunks (
            document_id uuid NOT NULL REFERENCES patent_documents(id),
            tokenizer_version text NOT NULL,
            field text NOT NULL,
            ordinal integer NOT NULL,
            tokens text NOT NULL,
            terms tsvector GENERATED ALWAYS AS (
                to_tsvector('simple'::regconfig, tokens)
            ) STORED,
            PRIMARY KEY (document_id, tokenizer_version, field, ordinal)
        )
    """)
    op.execute(
        "CREATE INDEX ix_patent_lexical_terms ON patent_lexical_chunks USING GIN (terms)"
    )


def downgrade():
    op.drop_table("patent_lexical_chunks")
