from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.db.base import Base
from app.db import models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline():
    from app.core.config import settings

    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connection = config.attributes.get("connection")
    if connection is not None:
        run_migrations(connection)
    else:
        from app.core.config import settings

        engine = create_engine(settings.database_url, pool_pre_ping=True)
        try:
            with engine.connect() as connection:
                run_migrations(connection)
        finally:
            engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
