"""Add owner-scoped audit log table for key account and research actions."""

from alembic import op

revision = "0018_audit_logs"
down_revision = "0017_legal_archive_refresh"
branch_labels = None
depends_on = None


def upgrade():
    # Records action types and opaque resource IDs only; never stores secrets or invention text.
    op.execute("""
        CREATE TABLE audit_logs (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            action text NOT NULL,
            resource_type text NOT NULL,
            resource_id text,
            outcome text NOT NULL CHECK (outcome IN ('success', 'denied', 'failed')),
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX ix_audit_logs_owner ON audit_logs (user_id, created_at DESC, id)"
    )
    op.execute("CREATE INDEX ix_audit_logs_recent ON audit_logs (created_at DESC, id)")


def downgrade():
    op.execute("DROP TABLE audit_logs")
