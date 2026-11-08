"""Add model-specific dense vectors for immutable document text."""

from alembic import op

revision = "0004_semantic"
down_revision = "0003_lexical"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE patent_embedding_models (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            provider text NOT NULL,
            model_name text NOT NULL,
            digest text NOT NULL CHECK (digest ~ '^[0-9a-f]{64}$'),
            pipeline text NOT NULL,
            dimensions integer NOT NULL CHECK (dimensions = 1024),
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (provider, model_name, digest, pipeline)
        )
    """)
    op.execute("""
        CREATE TABLE patent_dense_chunks (
            model_id bigint NOT NULL REFERENCES patent_embedding_models(id),
            document_id uuid NOT NULL REFERENCES patent_documents(id),
            field text NOT NULL,
            ordinal integer NOT NULL,
            char_start integer NOT NULL CHECK (char_start >= 0),
            char_end integer NOT NULL CHECK (char_end > char_start),
            embedding vector(1024) NOT NULL,
            PRIMARY KEY (model_id, document_id, field, ordinal, char_start)
        )
    """)


def downgrade():
    op.drop_table("patent_dense_chunks")
    op.drop_table("patent_embedding_models")
