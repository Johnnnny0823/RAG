from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

engine = create_engine(
    "postgresql+psycopg://",
    connect_args={
        "connect_timeout": 2,
        "options": "-c statement_timeout=2000 -c timezone=UTC",
    },
    poolclass=NullPool,
)


def check_database() -> None:
    with engine.connect() as connection:
        connection.exec_driver_sql(
            "SELECT '[1]'::vector <-> '[2]'::vector"
        ).scalar_one()
