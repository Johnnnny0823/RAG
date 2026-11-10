"""Record recent failed logins so repeated password guessing can be throttled."""

from alembic import op

revision = "0010_login_failures"
down_revision = "0009_session_message_cascade"
branch_labels = None
depends_on = None


def upgrade():
    # Only a digest of the submitted email is kept, also for unregistered addresses.
    op.execute("""
        CREATE TABLE login_failures (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            email_hash bytea NOT NULL,
            failed_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX ix_login_failures_recent ON login_failures (email_hash, failed_at)"
    )


def downgrade():
    op.execute("DROP TABLE login_failures")
