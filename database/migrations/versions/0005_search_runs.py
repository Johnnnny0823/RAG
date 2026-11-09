"""Add local accounts and owner-scoped search snapshots."""

from alembic import op

revision = "0005_search_runs"
down_revision = "0004_semantic"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE users (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            email text NOT NULL UNIQUE,
            password_salt bytea NOT NULL,
            password_hash bytea NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE auth_sessions (
            token_hash bytea PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES users(id),
            expires_at timestamptz NOT NULL
        )
    """)
    op.execute("""
        CREATE TABLE search_runs (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL REFERENCES users(id),
            request jsonb NOT NULL,
            settings jsonb NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX ix_search_runs_owner ON search_runs (user_id, created_at DESC, id)"
    )
    op.execute("""
        CREATE TABLE search_run_candidates (
            run_id uuid NOT NULL REFERENCES search_runs(id) ON DELETE CASCADE,
            position integer NOT NULL CHECK (position > 0),
            document_id uuid NOT NULL REFERENCES patent_documents(id),
            result jsonb NOT NULL,
            PRIMARY KEY (run_id, position),
            UNIQUE (run_id, document_id)
        )
    """)
    op.execute("""
        CREATE TABLE search_run_comparisons (
            run_id uuid NOT NULL,
            document_id uuid NOT NULL,
            result jsonb NOT NULL,
            PRIMARY KEY (run_id, document_id),
            FOREIGN KEY (run_id, document_id)
                REFERENCES search_run_candidates(run_id, document_id) ON DELETE CASCADE
        )
    """)


def downgrade():
    raise RuntimeError("Downgrade would discard accounts and private research records.")
