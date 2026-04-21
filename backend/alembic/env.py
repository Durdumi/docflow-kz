import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Импорт моделей для регистрации метаданных
import app.models.auth  # noqa: F401
from app.core.database import Base, TenantBase
from app.core.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# TENANT_SCHEMA env var — применяет миграции к конкретной tenant schema.
# Без него — применяются public миграции.
TENANT_SCHEMA = os.getenv("TENANT_SCHEMA", "")

if TENANT_SCHEMA:
    import app.models.documents  # noqa: F401
    target_metadata = TenantBase.metadata
else:
    target_metadata = Base.metadata


def do_run_migrations(connection: Connection) -> None:
    if TENANT_SCHEMA:
        # SET (не LOCAL) — session-level, чтобы alembic_version нашёлся в tenant schema
        connection.execute(text(f'SET search_path TO "{TENANT_SCHEMA}"'))

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table="alembic_version",
        include_schemas=False,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
