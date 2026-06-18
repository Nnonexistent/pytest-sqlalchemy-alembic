import os
from collections.abc import AsyncGenerator, Generator

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from .base import BaseDatabaseManager


class PostgresqlManager(BaseDatabaseManager):
    def make_connection(self) -> Generator[sa.Connection, None, None]:
        assert isinstance(self.engine, sa.Engine)
        with self.engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
            yield connection

    async def make_async_connection(self) -> AsyncGenerator[AsyncConnection]:
        assert isinstance(self.engine, AsyncEngine)
        async with self.engine.connect() as connection:
            new_connection = await connection.execution_options(isolation_level='AUTOCOMMIT')
            yield new_connection
            await new_connection.aclose()

    def make_test_engine_url(self, worker_id: str) -> sa.URL:
        url = self.engine.url
        return url.set(database=f'{url.database}_test_{worker_id}')

    def drop_test_database(self, connection: sa.Connection) -> None:
        self.check()
        connection.execute(sa.text(f'DROP DATABASE IF EXISTS {self.test_engine.url.database} WITH (FORCE);'))

    def create_test_database(self, connection: sa.Connection) -> None:
        self.check()
        # if connection to postgres is made with passwordless access using the 'trust' authentication method `url.username` may be empty
        owner = self.test_engine.url.username or os.environ.get('USER')
        connection.execute(sa.text(f'CREATE DATABASE {self.test_engine.url.database} OWNER {owner};'))

    def test_database_exists(self, connection: sa.Connection) -> bool:
        self.check()
        return (
            connection.scalar(
                sa.text('SELECT 1 FROM pg_catalog.pg_database WHERE datname = :dbname'),
                parameters={'dbname': self.test_engine.url.database},
            )
            is not None
        )
