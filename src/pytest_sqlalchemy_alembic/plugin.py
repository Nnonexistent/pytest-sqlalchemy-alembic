from __future__ import annotations

import contextlib
from collections.abc import AsyncGenerator, Generator

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
        dest='nomigrations',
        default=False,
        help='Disable alembic migrations on test setup',
    )
    parser.addini('sqlalchemy_session_maker', 'Import path to a sessionmaker instance', 'string', default=None)
    parser.addini('sqlalchemy_engine', 'Import path to SQLAlchemy engine instance', 'string', default=None)
    parser.addini('sqlalchemy_engine_url', 'SQLAlchemy engine URL', 'string', default=None)
    parser.addini('sqlalchemy_engine_kwargs', 'Import path to a dict containing engine kwargs', 'string', default=None)
    parser.addini('sqlalchemy_orm_loader', 'Import path to module or callable that loads all ORM necessary models', 'string', default=None)
    parser.addini('sqlalchemy_metadata', 'Import path to SQLAlchemy metadata. Usually `metadata` attribute of a declarative base class', 'string', default=None)
    parser.addini('sqlalchemy_engine_scope', 'Define at which scope test engine should activated (e.g., "session", "module")', 'string', default='session')


@pytest.fixture(scope='session')
def sqlalchemy_alembic_plugin_config(pytestconfig: pytest.Config) -> PluginConfig:
    """Configuration fixture for pytest-sqlalchemy-alembic plugin. Override it to configure plugin behavior."""  # noqa: D401
    return PluginConfig.build(pytestconfig)


def pytest_sessionstart(session: pytest.Session) -> None:
    if session.config.pluginmanager.hasplugin('asyncio'):
        globals()['setup_session_async'] = pytest.fixture(autouse=True, scope='session', name='sqlalchemy_alembic_setup_session')(setup_session_async)
        globals()['setup_module_async'] = pytest.fixture(autouse=True, scope='module', name='sqlalchemy_alembic_setup_module')(setup_module_async)
        globals()['setup_function_async'] = pytest.fixture(autouse=True, scope='function', name='sqlalchemy_alembic_setup_function')(setup_function_async)
    else:
        globals()['setup_session_sync'] = pytest.fixture(autouse=True, scope='session', name='sqlalchemy_alembic_setup_session')(setup_session_sync)
        globals()['setup_module_sync'] = pytest.fixture(autouse=True, scope='module', name='sqlalchemy_alembic_setup_module')(setup_module_sync)
        globals()['setup_function_sync'] = pytest.fixture(autouse=True, scope='function', name='sqlalchemy_alembic_setup_function')(setup_function_sync)


@contextlib.contextmanager
def _test_engine_ctx(cfg: PluginConfig, worker_id: str) -> Generator[BaseDatabaseManager, None, None]:
    database_manager = cfg.database_manager(cfg.engine)
    test_engine = database_manager.create_test_engine(worker_id, cfg.engine_kwargs)

    if cfg.session_maker is not None:
        cfg.session_maker.configure(bind=test_engine)

    yield database_manager

    if cfg.session_maker is not None:
        cfg.session_maker.configure(bind=cfg.engine)

    database_manager.dispose_test_engine()


@contextlib.asynccontextmanager
async def _async_test_engine_ctx(cfg: PluginConfig, worker_id: str) -> AsyncGenerator[BaseDatabaseManager]:
    database_manager = cfg.database_manager(cfg.engine)
    test_engine = database_manager.create_test_engine(worker_id, cfg.engine_kwargs)

    if cfg.session_maker is not None:
        cfg.session_maker.configure(bind=test_engine)

    yield database_manager

    if cfg.session_maker is not None:
        cfg.session_maker.configure(bind=cfg.engine)

    await database_manager.async_dispose_test_engine()


def setup_session_sync(
    pytestconfig: pytest.Config,
    sqlalchemy_alembic_plugin_config: PluginConfig,
) -> Generator[Engine | AsyncEngine, None, None]:
    """Session-scoped fixture to set up test database. Returns test engine instance."""
    cfg = sqlalchemy_alembic_plugin_config
    worker_id = resolve_worker_id(pytestconfig)

    with _test_engine_ctx(cfg, worker_id) as database_manager:
        database_manager.prepare_test_databases(create_db=pytestconfig.getoption('create_db'))

        if pytestconfig.getoption('nomigrations'):
            database_manager.create_tables(cfg.metadata)
        else:
            alembic_upgrade(database_manager.test_engine.url)

        yield database_manager.test_engine


async def setup_session_async(
    pytestconfig: pytest.Config,
    sqlalchemy_alembic_plugin_config: PluginConfig,
) -> AsyncGenerator[Engine | AsyncEngine, None]:
    """Session-scoped fixture to set up test database. Returns test engine instance."""
    cfg = sqlalchemy_alembic_plugin_config
    worker_id = resolve_worker_id(pytestconfig)

    async with _async_test_engine_ctx(cfg, worker_id) as database_manager:
        await database_manager.async_prepare_test_databases(create_db=pytestconfig.getoption('create_db'))

        if pytestconfig.getoption('nomigrations'):
            await database_manager.async_create_tables(cfg.metadata)
        else:
            alembic_upgrade(database_manager.test_engine.url)

        yield database_manager.test_engine


def setup_module_sync(
    pytestconfig: pytest.Config,
    sqlalchemy_alembic_plugin_config: PluginConfig,
) -> Generator[Engine | AsyncEngine | None, None, None]:
    """Module-scoped fixture to set up test database. Returns test engine instance."""
    cfg = sqlalchemy_alembic_plugin_config
    if cfg.engine_scope != 'module':
        yield None
        return

    worker_id = resolve_worker_id(pytestconfig)

    with _test_engine_ctx(cfg, worker_id) as database_manager:
        yield database_manager.test_engine


async def setup_module_async(
    pytestconfig: pytest.Config,
    sqlalchemy_alembic_plugin_config: PluginConfig,
) -> AsyncGenerator[Engine | AsyncEngine | None, None]:
    """Module-scoped fixture to set up test database. Returns test engine instance."""
    cfg = sqlalchemy_alembic_plugin_config
    if cfg.engine_scope != 'module':
        yield None
        return

    worker_id = resolve_worker_id(pytestconfig)

    async with _async_test_engine_ctx(cfg, worker_id) as database_manager:
        yield database_manager.test_engine


def setup_function_sync(
    pytestconfig: pytest.Config,
    sqlalchemy_alembic_plugin_config: PluginConfig,
) -> Generator[Engine | AsyncEngine | None, None, None]:
    """Function-scoped fixture to set up test database. Returns test engine instance."""
    cfg = sqlalchemy_alembic_plugin_config
    if cfg.engine_scope != 'function':
        yield None
        return

    worker_id = resolve_worker_id(pytestconfig)

    with _test_engine_ctx(cfg, worker_id) as database_manager:
        yield database_manager.test_engine


async def setup_function_async(
    pytestconfig: pytest.Config,
    sqlalchemy_alembic_plugin_config: PluginConfig,
) -> AsyncGenerator[Engine | AsyncEngine | None, None]:
    """Function-scoped fixture to set up test database. Returns test engine instance."""
    cfg = sqlalchemy_alembic_plugin_config
    if cfg.engine_scope != 'function':
        yield None
        return

    worker_id = resolve_worker_id(pytestconfig)

    async with _async_test_engine_ctx(cfg, worker_id) as database_manager:
        yield database_manager.test_engine
