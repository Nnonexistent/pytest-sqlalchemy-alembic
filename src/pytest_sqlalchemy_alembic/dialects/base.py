import abc
import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator, Generator, Iterable
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

_logger = logging.getLogger('pytest-sqlalchemy-alembic')


class BaseDatabaseManager(abc.ABC):
    test_engine: sa.Engine | AsyncEngine

    def __init__(self, engine: sa.Engine | AsyncEngine) -> None:
        self.engine = engine

    def make_connection(self) -> Generator[sa.Connection, None, None]:
        assert isinstance(self.engine, sa.Engine)
        with self.engine.connect() as connection:
            yield connection

    async def make_async_connection(self) -> AsyncGenerator[AsyncConnection]:
        assert isinstance(self.engine, AsyncEngine)
        async with self.engine.connect() as connection:
            yield connection

    @abc.abstractmethod
    def make_test_engine_url(self, worker_id: str) -> sa.URL:
        raise NotImplementedError()

    @abc.abstractmethod
    def drop_test_database(self, connection: sa.Connection) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def create_test_database(self, connection: sa.Connection) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def test_database_exists(self, connection: sa.Connection) -> bool:
        raise NotImplementedError()

    def check(self) -> None:
        assert getattr(self, 'test_engine', None) is not None, 'Test engine has not been created yet. Call `create_test_engine` first.'

    def create_test_engine(self, worker_id: str, engine_kwargs: dict[str, Any]) -> sa.Engine | AsyncEngine:
        test_db_url = self.make_test_engine_url(worker_id)
        if isinstance(self.engine, AsyncEngine):
            self.test_engine = create_async_engine(test_db_url, **engine_kwargs)
            return self.test_engine
        else:
            self.test_engine = sa.create_engine(test_db_url, **engine_kwargs)
            return self.test_engine

    def prepare_test_databases(self, *, create_db: bool) -> None:
        if isinstance(self.test_engine, AsyncEngine):
            asyncio.run(self._async_prepare_test_databases(create_db=create_db))
        else:
            self._sync_prepare_test_databases(create_db=create_db)

    async def async_prepare_test_databases(self, *, create_db: bool) -> None:
        if isinstance(self.test_engine, AsyncEngine):
            await self._async_prepare_test_databases(create_db=create_db)
        else:
            self._sync_prepare_test_databases(create_db=create_db)

    def create_tables(self, metadata: Iterable[sa.MetaData]) -> None:
        _logger.info('Creating tables for %s', self.test_engine.url.database)
        if isinstance(self.test_engine, AsyncEngine):
            asyncio.run(self._async_create_all(metadata))
        else:
            for m in metadata:
                m.create_all(bind=self.test_engine)

    async def async_create_tables(self, metadata: Iterable[sa.MetaData]) -> None:
        _logger.info('Creating tables for %s', self.test_engine.url.database)
        if isinstance(self.test_engine, AsyncEngine):
            await self._async_create_all(metadata)
        else:
            for m in metadata:
                m.create_all(bind=self.test_engine)

    def dispose_test_engine(self) -> None:
        if isinstance(self.test_engine, AsyncEngine):
            asyncio.run(self.test_engine.dispose())
        else:
            self.test_engine.dispose()

    async def async_dispose_test_engine(self) -> None:
        if isinstance(self.test_engine, AsyncEngine):
            await self.test_engine.dispose()
        else:
            self.test_engine.dispose()

    async def _async_create_all(self, metadata: Iterable[sa.MetaData]) -> None:
        assert isinstance(self.test_engine, AsyncEngine)
        async with self.test_engine.begin() as conn:
            for m in metadata:
                await conn.run_sync(m.create_all)

    def _sync_prepare_test_databases(self, *, create_db: bool) -> None:
        ctx = contextlib.contextmanager(self.make_connection)
        with ctx() as connection:
            if create_db:
                _logger.info('Re-creating test database %s', self.test_engine.url.database)
                self.drop_test_database(connection)
                self.create_test_database(connection)
            elif self.test_database_exists(connection):
                _logger.info('Re-using existing test database %s', self.test_engine.url.database)
            else:
                _logger.info('Creating a new test database %s', self.test_engine.url.database)
                self.create_test_database(connection)

    async def _async_prepare_test_databases(self, *, create_db: bool) -> None:
        ctx = contextlib.asynccontextmanager(self.make_async_connection)
        async with ctx() as connection:
            if create_db:
                _logger.info('Re-creating test database %s', self.test_engine.url.database)
                await connection.run_sync(self.drop_test_database)
                await connection.run_sync(self.create_test_database)
            elif await connection.run_sync(self.test_database_exists):
                _logger.info('Re-using existing test database %s', self.test_engine.url.database)
            else:
                _logger.info('Creating a new test database %s', self.test_engine.url.database)
                await connection.run_sync(self.create_test_database)
