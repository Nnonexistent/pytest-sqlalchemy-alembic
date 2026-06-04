from __future__ import annotations

import logging
from collections.abc import Generator

import pytest
from sqlalchemy import Engine

from .config import PluginConfig
from .utils import alembic_upgrade, resolve_worker_id

_logger = logging.getLogger('pytest-sqlalchemy-alembic')


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


@pytest.fixture(scope='session')
def sqlalchemy_alembic_plugin_config(pytestconfig: pytest.Config) -> PluginConfig:
    return PluginConfig.build(pytestconfig)


@pytest.fixture(autouse=True, scope='session')
def sqlalchemy_alembic_setup(
    pytestconfig: pytest.Config,
    sqlalchemy_alembic_plugin_config: PluginConfig,
) -> Generator[Engine, None, None]:
    cfg = sqlalchemy_alembic_plugin_config
    database_manager = cfg.database_manager(cfg.engine)
    worker_id = resolve_worker_id(pytestconfig)

    test_engine = database_manager.create_test_engine(worker_id, cfg.engine_kwargs)

    with database_manager:
        if pytestconfig.getoption('create_db'):
            _logger.info('Re-creating test database %s', test_engine.url.database)
            database_manager.drop_test_database()
            database_manager.create_test_database()
        elif database_manager.test_database_exists():
            _logger.info('Re-using existing test database %s', test_engine.url.database)
        else:
            _logger.info('Creating a new test database %s', test_engine.url.database)
            database_manager.create_test_database()

    if pytestconfig.getoption('nomigrations'):
        _logger.info('Creating tables for %s', test_engine.url.database)
        for metadata in cfg.metadata:
            metadata.create_all(bind=test_engine)
    else:
        _logger.info('Migrating database %s', test_engine.url.database)
        alembic_upgrade(test_engine)

    if cfg.session_maker is not None:
        cfg.session_maker.configure(bind=test_engine)

    yield test_engine

    if cfg.session_maker is not None:
        cfg.session_maker.configure(bind=cfg.engine)
