from __future__ import annotations

import abc
import os

import sqlalchemy as sa
from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql.psycopg2 import PGDialect_psycopg2
from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.engine.url import URL
from typing_extensions import Self


class DatabaseManager(abc.ABC):
    def __init__(self, engine: Engine, url: URL) -> None:
        self.engine = engine
        self.url = url

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: B027
        pass

    @abc.abstractmethod
    def drop(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def create(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def exists(self) -> bool:
        raise NotImplementedError()


class SQLiteDatabaseManager(DatabaseManager):
    def _is_in_memory(self) -> bool:
        return not self.url.database or self.url.database == ":memory:"

    def drop(self) -> None:
        if self._is_in_memory():
            return

        assert self.url.database is not None
        if os.path.exists(self.url.database):
            os.remove(self.url.database)

    def create(self) -> None:
        # SQLite creates the database file automatically on first connection
        pass

    def exists(self) -> bool:
        if self._is_in_memory():
            return True

        assert self.url.database is not None
        return os.path.exists(self.url.database)


class PostgresqlDatabaseManager(DatabaseManager):
    def __enter__(self) -> Self:
        self.connection = self.engine.connect().execution_options(isolation_level="AUTOCOMMIT")
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.connection.close()

    def drop(self) -> None:
        self.connection.execute(sa.text(f"DROP DATABASE IF EXISTS {self.url.database} WITH (FORCE);"))

    def create(self) -> None:
        self.connection.execute(sa.text(f"CREATE DATABASE {self.url.database} OWNER {self.url.username};"))

    def exists(self) -> bool:
        return (
            self.connection.scalar(
                sa.text("SELECT 1 FROM pg_catalog.pg_database WHERE datname = :dbname"),
                parameters={"dbname": self.url.database},
            )
            is not None
        )


MANAGERS = {
    SQLiteDialect_pysqlite: SQLiteDatabaseManager,
    PGDialect_psycopg2: PostgresqlDatabaseManager,
}


def get_database_manager(dialect: type[Dialect]) -> type[DatabaseManager]:
    if dialect not in MANAGERS:
        msg = f"No DatabaseManager found for dialect {dialect.__name__}"
        raise ValueError(msg)

    return MANAGERS[dialect]
