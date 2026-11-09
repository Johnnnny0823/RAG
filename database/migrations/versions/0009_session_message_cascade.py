"""Remove private messages when their research session is deleted."""

from alembic import op

revision = "0009_session_message_cascade"
down_revision = "0008_research_sessions"
branch_labels = None
depends_on = None


def replace_message_foreign_key(ondelete=None):
    op.drop_constraint("messages_session_id_fkey", "messages", type_="foreignkey")
    op.create_foreign_key(
        "messages_session_id_fkey",
        "messages",
        "sessions",
        ["session_id"],
        ["id"],
        ondelete=ondelete,
    )


def upgrade():
    replace_message_foreign_key("CASCADE")


def downgrade():
    replace_message_foreign_key()
