from __future__ import annotations

import contextlib
from collections.abc import AsyncGenerator, Generator, Sequence

import pytest
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

from pytest_sqlalchemy_alembic.dialects.base import BaseDatabaseManager

from .config import PluginConfig
from .utils import alembic_upgrade, resolve_worker_id


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('sqlalchemy')
    group.addoption(
        '--createdb',
        '--create-db',
        action='store_true',
        dest='create_db',
        default=False,
        help='Re-create the database, even if it exists.',
    )
    group.addoption(
        '--nomigrations',
        '--no-migrations',
        action='store_true',
        dest='no_migrations',
        default=False,
        help='Disable alembic migrations on test setup',
    )
    parser.addini('sqlalchemy_alembic_configs', '', 'linelist', default=[])


@pytest.fixture(scope='session')
def sqlalchemy_alembic_plugin_configs(pytestconfig: pytest.Config) -> list[PluginConfig]:
    """Extension point to override config values for pytest-sqlalchemy-alembic plugin from python context."""
    return PluginConfig.build_list(pytestconfig)


def pytest_sessionstart(session: pytest.Session) -> None:
    if session.config.pluginmanager.hasplugin('asyncio'):
        from pytest_asyncio import fixture as asyncio_fixture

        globals()['setup_session_async'] = asyncio_fixture(
            autouse=True,
            scope='session',
            loop_scope='session',
            name='sqlalchemy_alembic_setup_session',
        )(setup_session_async)
        globals()['setup_function_async'] = pytest.fixture(autouse=True, scope='function', name='sqlalchemy_alembic_setup_function')(setup_function_async)
    else:
        globals()['setup_session_sync'] = pytest.fixture(autouse=True, scope='session', name='sqlalchemy_alembic_setup_session')(setup_session_sync)
        globals()['setup_function_sync'] = pytest.fixture(autouse=True, scope='function', name='sqlalchemy_alembic_setup_function')(setup_function_sync)


@contextlib.contextmanager
def _test_engine_ctx(cfg: PluginConfig, worker_id: str, *, db_management: bool) -> Generator[BaseDatabaseManager, None, None]:
    database_manager = cfg.database_manager(cfg.engine)
    test_engine = database_manager.create_test_engine(worker_id, cfg.engine_kwargs)

    if db_management:
        database_manager.prepare_test_databases(create_db=cfg.create_db)
        if cfg.no_migrations:
            database_manager.create_tables(cfg.metadata)
        else:
            alembic_upgrade(database_manager.test_engine.url)

    if cfg.session_maker is not None:
        cfg.session_maker.configure(bind=test_engine)

    yield database_manager

    if cfg.session_maker is not None:
        cfg.session_maker.configure(bind=cfg.engine)

    database_manager.dispose_test_engine()


@contextlib.asynccontextmanager
async def _async_test_engine_ctx(cfg: PluginConfig, worker_id: str, *, db_management: bool) -> AsyncGenerator[BaseDatabaseManager]:
    database_manager = cfg.database_manager(cfg.engine)
    test_engine = database_manager.create_test_engine(worker_id, cfg.engine_kwargs)

    if db_management:
        await database_manager.async_prepare_test_databases(create_db=cfg.create_db)
        if cfg.no_migrations:
            await database_manager.async_create_tables(cfg.metadata)
        else:
            alembic_upgrade(database_manager.test_engine.url)

    if cfg.session_maker is not None:
        cfg.session_maker.configure(bind=test_engine)

    yield database_manager

    if cfg.session_maker is not None:
        cfg.session_maker.configure(bind=cfg.engine)

    await database_manager.async_dispose_test_engine()


def setup_session_sync(
    pytestconfig: pytest.Config,
    sqlalchemy_alembic_plugin_configs: list[PluginConfig],
) -> Generator[Sequence[Engine | AsyncEngine]]:
    """Session-scoped fixture to set up test database. Returns a sequence of test engine instances."""
    worker_id = resolve_worker_id(pytestconfig)

    with contextlib.ExitStack() as stack:
        test_engines = []

        for cfg in sqlalchemy_alembic_plugin_configs:
            database_manager = stack.enter_context(
                _test_engine_ctx(cfg, worker_id, db_management=not cfg.skip_db_management),
            )

            test_engines.append(database_manager.test_engine)

        yield tuple(test_engines)


async def setup_session_async(
    pytestconfig: pytest.Config,
    sqlalchemy_alembic_plugin_configs: list[PluginConfig],
) -> AsyncGenerator[Sequence[Engine | AsyncEngine], None]:
    """Session-scoped fixture to set up test database. Returns a sequence of test engine instances."""
    worker_id = resolve_worker_id(pytestconfig)

    async with contextlib.AsyncExitStack() as stack:
        test_engines = []

        for cfg in sqlalchemy_alembic_plugin_configs:
            database_manager = await stack.enter_async_context(
                _async_test_engine_ctx(cfg, worker_id, db_management=not cfg.skip_db_management),
            )

            test_engines.append(database_manager.test_engine)

        yield tuple(test_engines)


def setup_function_sync(
    pytestconfig: pytest.Config,
    sqlalchemy_alembic_plugin_configs: list[PluginConfig],
) -> Generator[Sequence[Engine | AsyncEngine | None], None, None]:
    """Function-scoped fixture to set up test database. Returns a sequence of test engine instances."""
    worker_id = resolve_worker_id(pytestconfig)

    with contextlib.ExitStack() as stack:
        test_engines: list[Engine | AsyncEngine | None] = []

        for cfg in sqlalchemy_alembic_plugin_configs:
            if cfg.scope != 'function':
                test_engines.append(None)
                continue

            database_manager = stack.enter_context(
                _test_engine_ctx(cfg, worker_id, db_management=False),
            )

            test_engines.append(database_manager.test_engine)

        yield tuple(test_engines)


async def setup_function_async(
    pytestconfig: pytest.Config,
    sqlalchemy_alembic_plugin_configs: list[PluginConfig],
) -> AsyncGenerator[Sequence[Engine | AsyncEngine | None], None]:
    """Function-scoped fixture to set up test database. Returns a sequence of test engine instances."""
    worker_id = resolve_worker_id(pytestconfig)

    async with contextlib.AsyncExitStack() as stack:
        test_engines: list[Engine | AsyncEngine | None] = []

        for cfg in sqlalchemy_alembic_plugin_configs:
            if cfg.scope != 'function':
                test_engines.append(None)
                continue

            database_manager = await stack.enter_async_context(
                _async_test_engine_ctx(cfg, worker_id, db_management=False),
            )

            test_engines.append(database_manager.test_engine)

        yield tuple(test_engines)
