from __future__ import annotations

import logging
from collections.abc import Generator

import pytest
from alembic.command import upgrade as alembic_upgrade
from alembic.config import CommandLine as AlembicCli
from alembic.config import Config as AlembicConfig
from sqlalchemy import Engine

from .config import PluginConfig

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
    parser.addini('sqlalchemy_sessionmaker', 'Import path to sessionmaker (required)', 'string', default=None)
    parser.addini('sqlalchemy_engine', 'Import path to engine', 'string', default=None)
    parser.addini('sqlalchemy_engine_url', 'Engine URL', 'string', default=None)
    parser.addini('sqlalchemy_engine_kwargs', 'Import path to engine kwargs', 'string', default=None)
    parser.addini('sqlalchemy_orm_loader', 'Import path to module or callable that loads all ORM models', 'string', default=None)
    parser.addini('sqlalchemy_declarative_base', 'Import path to declarative base class for SQLAlchemy ORM models (required)', 'string', default=None)


@pytest.fixture(scope='session')
def pytest_sqlalchemy_alembic_plugin_config(config: pytest.Config) -> PluginConfig:
    return PluginConfig.build(config)


@pytest.fixture(autouse=True, scope='session')
def db_setup(
    request: pytest.FixtureRequest,
    worker_id: str,
    pytest_sqlalchemy_alembic_plugin_config: PluginConfig,
) -> Generator[Engine, None, None]:
    cfg = pytest_sqlalchemy_alembic_plugin_config
    backend = cfg.dialect_backend

    test_engine = backend.create_test_engine(cfg.engine, worker_id, cfg.engine_kwargs)

    if request.config.getvalue('create_db'):
        backend.recreate_test_database(cfg.engine, test_engine)
    else:
        backend.reuse_or_create_test_database(cfg.engine, test_engine)

    if request.config.getvalue('nomigrations'):
        _logger.info('Creating tables for %s', test_engine.url.database)
        cfg.metadata.create_all(bind=test_engine)
    else:
        _logger.info('Migrating database %s', test_engine.url.database)
        options = AlembicCli().parser.parse_args(['upgrade', 'head'])
        alembic_config = AlembicConfig(
            file_=options.config,
            ini_section=options.name,
            cmd_opts=options,
        )
        alembic_config.set_main_option('sqlalchemy.url', test_engine.url.render_as_string(hide_password=False))
        alembic_upgrade(alembic_config, 'head')

    cfg.session_maker.configure(bind=test_engine)

    yield test_engine

    cfg.session_maker.configure(bind=cfg.engine)
