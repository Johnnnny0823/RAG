from alembic import context

from services.api.db import engine

if context.is_offline_mode():
    context.configure(dialect_name="postgresql")
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
