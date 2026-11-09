"""Store owner-scoped research conversations separately from search runs."""

from alembic import op

revision = "0008_research_sessions"
down_revision = "0007_saved_patents"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE sessions (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id uuid NOT NULL REFERENCES projects(id),
            title text NOT NULL CHECK (char_length(btrim(title)) BETWEEN 1 AND 120),
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX ix_sessions_project ON sessions (project_id, created_at DESC, id)"
    )
    op.execute("""
        CREATE TABLE messages (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id uuid NOT NULL REFERENCES sessions(id),
            sequence bigint GENERATED ALWAYS AS IDENTITY,
            role text NOT NULL CHECK (role IN ('user', 'assistant')),
            content jsonb NOT NULL CHECK (
                (role = 'user' AND jsonb_typeof(content) = 'string') OR
                (role = 'assistant' AND jsonb_typeof(content) = 'object')
            ),
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (session_id, sequence)
        )
    """)


def downgrade():
    raise RuntimeError("Downgrade would discard private research sessions.")
