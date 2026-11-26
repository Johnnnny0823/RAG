"""Allow legal gazette archive recovery in the refresh checkpoint table."""

from alembic import op

revision = "0017_legal_archive_refresh"
down_revision = "0016_archive_refresh"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "archive_refresh_checkpoints_stage_check",
        "archive_refresh_checkpoints",
        type_="check",
    )
    op.create_check_constraint(
        "archive_refresh_checkpoints_stage_check",
        "archive_refresh_checkpoints",
        "stage IN ('publication', 'grant', 'legal')",
    )


def downgrade():
    op.drop_constraint(
        "archive_refresh_checkpoints_stage_check",
        "archive_refresh_checkpoints",
        type_="check",
    )
    op.create_check_constraint(
        "archive_refresh_checkpoints_stage_check",
        "archive_refresh_checkpoints",
        "stage IN ('publication', 'grant')",
    )
