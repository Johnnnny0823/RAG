"""Allow verified legal events for invention, utility model, and design grants."""

import sqlalchemy as sa
from alembic import op

revision = "0022_legal_event_grant_types"
down_revision = "0021_gazette_pdf_search"
branch_labels = None
depends_on = None

CERTIFICATE_TABLES = ("patent_legal_events", "legal_event_catalog")
APPLICATION_CHECK = "legal_event_catalog_application_no_check"


def upgrade():
    for table in CERTIFICATE_TABLES:
        constraint = f"{table}_certificate_no_check"
        op.drop_constraint(constraint, table, type_="check")
        op.create_check_constraint(
            constraint, table, "certificate_no ~ '^[IMD][0-9]+$'"
        )
    op.drop_constraint(APPLICATION_CHECK, "legal_event_catalog", type_="check")
    op.create_check_constraint(
        APPLICATION_CHECK,
        "legal_event_catalog",
        "application_no ~ '^[0-9]{9}$' OR (certificate_no LIKE 'D%' AND application_no ~ '^[0-9]{3}3[0-9]{5}D(0[1-9]|[1-9][0-9])$')",
    )


def downgrade():
    conn = op.get_bind()
    for table in CERTIFICATE_TABLES:
        if conn.execute(
            sa.text(
                f"SELECT EXISTS (SELECT 1 FROM {table} WHERE certificate_no !~ '^I[0-9]+$')"
            )
        ).scalar_one():
            raise RuntimeError(
                "Downgrade would discard supported utility model or design events"
            )
    for table in CERTIFICATE_TABLES:
        constraint = f"{table}_certificate_no_check"
        op.drop_constraint(constraint, table, type_="check")
        op.create_check_constraint(constraint, table, "certificate_no ~ '^I[0-9]+$'")
    op.drop_constraint(APPLICATION_CHECK, "legal_event_catalog", type_="check")
    op.create_check_constraint(
        APPLICATION_CHECK, "legal_event_catalog", "application_no ~ '^[0-9]{9}$'"
    )
