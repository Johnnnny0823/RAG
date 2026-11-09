"""Store patent-version bookmarks and private project notes."""

from alembic import op

revision = "0007_saved_patents"
down_revision = "0006_projects"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE saved_patents (
            project_id uuid NOT NULL REFERENCES projects(id),
            document_id uuid NOT NULL REFERENCES patent_documents(id),
            note text NOT NULL DEFAULT '' CHECK (char_length(note) <= 4000),
            created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (project_id, document_id)
        )
    """)
    op.execute("""
        CREATE INDEX ix_saved_patents_project_order
        ON saved_patents (project_id, created_at DESC, document_id)
    """)


def downgrade():
    raise RuntimeError("Downgrade would discard private patent bookmarks and notes.")
