import asyncio

from example_project_async.config import settings
from example_project_async.db import Base
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

__import__('example_project_async.models')

config = context.config
config.set_main_option('.', '.')  # workaround to create a config object

target_metadata = Base.metadata

if not config.get_main_option('sqlalchemy.url'):
    config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)


def run_migrations_offline() -> None:
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        compare_type=True,
        compare_server_default=True,
        transaction_per_migration=True,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(sync_run_migrations)

    await connectable.dispose()


def sync_run_migrations(connection: Connection) -> None:
    context.configure(
        compare_type=True,
        compare_server_default=True,
        transaction_per_migration=True,
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
