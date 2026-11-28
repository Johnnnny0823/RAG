from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from services.api.provision_db_role import CORPUS_TABLES, RESEARCH_GRANTS

READINESS_TABLES = (*CORPUS_TABLES, *RESEARCH_GRANTS)

engine = create_engine(
    "postgresql+psycopg://",
    connect_args={
        "connect_timeout": 2,
        "options": "-c statement_timeout=2000 -c timezone=UTC",
    },
    poolclass=NullPool,
)


class DatabaseSchemaUnavailable(SQLAlchemyError):
    pass


def check_database() -> None:
    with engine.connect() as connection:
        ready = connection.exec_driver_sql(
            """SELECT ('[1]'::vector <-> '[2]'::vector) = 1
                       AND has_schema_privilege('public', 'USAGE')
                       AND bool_and(has_table_privilege('public.' || quote_ident(name), 'SELECT'))
                FROM unnest(%s::text[]) AS required(name)""",
            (list(READINESS_TABLES),),
        ).scalar_one()
        if ready is not True:
            raise DatabaseSchemaUnavailable("Runtime database schema is unavailable")
