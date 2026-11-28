"""Track operator-run official imports and indexing independently of batch metadata."""

from alembic import op

revision = "0014_ingestion_jobs"
down_revision = "0013_generated_reports"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE ingestion_jobs (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            batch_key text NOT NULL CHECK (batch_key ~ '^[0-9]{6}$'),
            status text NOT NULL DEFAULT 'running'
                CHECK (status IN ('running', 'succeeded', 'partial', 'failed', 'interrupted')),
            stage text NOT NULL DEFAULT 'import'
                CHECK (stage IN ('import', 'lexical', 'semantic')),
            counts jsonb NOT NULL DEFAULT '{}',
            started_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            finished_at timestamptz,
            CHECK ((finished_at IS NULL) = (status = 'running'))
        )
    """)
    op.execute(
        "CREATE INDEX ix_ingestion_jobs_recent ON ingestion_jobs (started_at DESC, id)"
    )


def downgrade():
    op.drop_table("ingestion_jobs")
