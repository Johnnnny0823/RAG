"""Group private search snapshots under owner-scoped projects."""

from alembic import op

revision = "0006_projects"
down_revision = "0005_search_runs"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE projects (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id uuid NOT NULL REFERENCES users(id),
            name text NOT NULL CHECK (char_length(btrim(name)) BETWEEN 1 AND 120),
            description text NOT NULL DEFAULT '' CHECK (char_length(description) <= 2000),
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (owner_user_id, id)
        )
    """)
    op.execute(
        "CREATE INDEX ix_projects_owner ON projects (owner_user_id, created_at DESC, id)"
    )
    op.execute("""
        ALTER TABLE search_runs ADD COLUMN project_id uuid,
        ADD CONSTRAINT fk_search_runs_owner_project
            FOREIGN KEY (user_id, project_id) REFERENCES projects (owner_user_id, id)
    """)
    op.execute("""
        CREATE INDEX ix_search_runs_project
        ON search_runs (user_id, project_id, created_at DESC, id)
        WHERE project_id IS NOT NULL
    """)


def downgrade():
    raise RuntimeError(
        "Downgrade would discard private projects and search assignments."
    )
