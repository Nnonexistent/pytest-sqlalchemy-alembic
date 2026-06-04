import os
from typing import Any

import sqlalchemy as sa
from sqlalchemy import Engine, create_engine
from typing_extensions import Self

from .base import BaseDatabaseManager


class PostgresqlPsycopgManager(BaseDatabaseManager):
    def __enter__(self) -> Self:
        self.connection = self.engine.connect().execution_options(isolation_level='AUTOCOMMIT')
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.connection.close()

    def create_test_engine(self, worker_id: str, engine_kwargs: dict[str, Any]) -> Engine:
        url = self.engine.url
        test_db_url = url.set(database=f'{url.database}_test_{worker_id}')
        self.test_engine = create_engine(test_db_url, **engine_kwargs)
        return self.test_engine

    def drop_test_database(self) -> None:
        self.check()
        self.connection.execute(sa.text(f'DROP DATABASE IF EXISTS {self.test_engine.url.database} WITH (FORCE);'))

    def create_test_database(self) -> None:
        # if connection to postgres is made with passwordless access using the 'trust' authentication method `url.username` may be empty
        owner = self.test_engine.url.username or os.environ.get('USER')
        self.connection.execute(sa.text(f'CREATE DATABASE {self.test_engine.url.database} OWNER {owner};'))

    def test_database_exists(self) -> bool:
        return (
            self.connection.scalar(
                sa.text('SELECT 1 FROM pg_catalog.pg_database WHERE datname = :dbname'),
                parameters={'dbname': self.test_engine.url.database},
            )
            is not None
        )

    def check(self):
        super().check()
        assert getattr(self, 'connection', None) is not None, 'Connection has not been created yet. Use calls inside context manager'
