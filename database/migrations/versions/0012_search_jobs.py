"""Persist resumable status for background searches."""

from alembic import op

revision = "0012_search_jobs"
down_revision = "0011_claim_dependencies"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE search_jobs (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            request jsonb,
            status text NOT NULL DEFAULT 'queued'
                CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
            run_id uuid REFERENCES search_runs(id) ON DELETE CASCADE,
            error_code text,
            created_at timestamptz NOT NULL DEFAULT now(),
            started_at timestamptz,
            finished_at timestamptz,
            CHECK ((request IS NOT NULL) = (status IN ('queued', 'running'))),
            CHECK ((finished_at IS NOT NULL) = (status IN ('succeeded', 'failed', 'cancelled'))),
            CHECK ((run_id IS NOT NULL) = (status = 'succeeded')),
            CHECK ((error_code IS NOT NULL) = (status = 'failed'))
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX ix_search_jobs_active_owner ON search_jobs (user_id)
        WHERE status IN ('queued', 'running')
    """)
    op.create_index(
        "ix_search_jobs_queue", "search_jobs", ["status", "created_at", "id"]
    )
    op.create_index("ix_search_jobs_user", "search_jobs", ["user_id"])
    op.create_index("ix_search_jobs_run", "search_jobs", ["run_id"])
    op.create_index("ix_search_jobs_finished", "search_jobs", ["finished_at"])


def downgrade():
    op.drop_table("search_jobs")
