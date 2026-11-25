"""Store short-lived private PDF jobs and artifacts."""

from alembic import op

revision = "0013_generated_reports"
down_revision = "0012_search_jobs"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE generated_reports (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id uuid NOT NULL REFERENCES search_runs(id) ON DELETE CASCADE,
            status text NOT NULL DEFAULT 'queued'
                CHECK (status IN ('queued', 'running', 'succeeded', 'failed')),
            pdf bytea CHECK (octet_length(pdf) BETWEEN 1 AND 8388608),
            created_at timestamptz NOT NULL DEFAULT now(),
            started_at timestamptz,
            finished_at timestamptz,
            CHECK ((finished_at IS NOT NULL) = (status IN ('succeeded', 'failed'))),
            CHECK ((pdf IS NOT NULL) = (status = 'succeeded'))
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX ix_generated_reports_active_run ON generated_reports (run_id)
        WHERE status IN ('queued', 'running')
    """)
    op.create_index(
        "ix_generated_reports_queue",
        "generated_reports",
        ["status", "created_at", "id"],
    )
    op.create_index("ix_generated_reports_run", "generated_reports", ["run_id"])
    op.create_index(
        "ix_generated_reports_finished", "generated_reports", ["finished_at"]
    )


def downgrade():
    op.drop_table("generated_reports")
