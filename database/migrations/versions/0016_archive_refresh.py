"""Track verified archive refresh completion per issue and import configuration."""

from alembic import op

revision = "0016_archive_refresh"
down_revision = "0015_legal_events"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE archive_refresh_checkpoints (
            stage text NOT NULL CHECK (stage IN ('publication', 'grant')),
            archive_year text NOT NULL CHECK (archive_year ~ '^[0-9]{3}$'),
            issue text NOT NULL CHECK (issue ~ '^[0-9]{6}$'),
            configuration_hash text NOT NULL CHECK (configuration_hash ~ '^[0-9a-f]{64}$'),
            completed_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (stage, archive_year, configuration_hash, issue)
        )
    """)


def downgrade():
    op.drop_table("archive_refresh_checkpoints")
