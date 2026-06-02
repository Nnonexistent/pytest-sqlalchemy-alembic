import logging
from typing import Any

import sqlalchemy as sa
from sqlalchemy import Engine, create_engine

from .base import DialectBackend

_logger = logging.getLogger('pytest-sqlalchemy-alembic')


class PostgresqlPsycopgBackend(DialectBackend):
    @classmethod
    def create_test_engine(cls, engine: Engine, worker_id: str, engine_kwargs: dict[str, Any]) -> Engine:
        url = engine.url
        test_db_url = url.set(database=f'{url.database}_test_{worker_id}')
        return create_engine(test_db_url, **engine_kwargs)

    @classmethod
    def recreate_test_database(cls, base_engine: Engine, test_engine: Engine) -> None:
        connection = base_engine.connect().execution_options(isolation_level='AUTOCOMMIT')
        with connection:
            _logger.info('Recreating database: %s', test_engine.url.database)
            connection.execute(sa.text(f'DROP DATABASE IF EXISTS {test_engine.url.database} WITH (FORCE);'))
            connection.execute(sa.text(f'CREATE DATABASE {test_engine.url.database} OWNER {test_engine.url.username};'))

    @classmethod
    def reuse_or_create_test_database(cls, base_engine: Engine, test_engine: Engine) -> None:
        connection = base_engine.connect().execution_options(isolation_level='AUTOCOMMIT')
        with connection:
            database_exists = connection.scalar(
                sa.text('SELECT 1 FROM pg_catalog.pg_database WHERE datname = :dbname'),
                parameters={'dbname': test_engine.url.database},
            )
            if database_exists is None:
                _logger.info('Creating database: %s', test_engine.url.database)
                connection.execute(sa.text(f'CREATE DATABASE {test_engine.url.database} OWNER {test_engine.url.username};'))
            else:
                _logger.info('Reusing database: %s', test_engine.url.database)
