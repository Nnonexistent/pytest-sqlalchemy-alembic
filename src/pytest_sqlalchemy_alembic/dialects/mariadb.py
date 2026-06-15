from contextlib import suppress
from typing import Any

import sqlalchemy as sa
from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import OperationalError
from typing_extensions import Self

from .base import BaseDatabaseManager


class MariaDBManager(BaseDatabaseManager):
    def __enter__(self) -> Self:
        self.connection = self.engine.connect()
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
        connection_ids = self.connection.execute(
            sa.text("""
                SELECT id FROM information_schema.processlist
                WHERE db = :db_name AND id != CONNECTION_ID()
            """),
            {'db_name': self.test_engine.url.database},
        )

        for cid in [row[0] for row in connection_ids.fetchall()]:
            with suppress(OperationalError):  # connection may already be gone
                self.connection.execute(sa.text(f'KILL CONNECTION {cid}'))

        self.connection.execute(sa.text(f'DROP DATABASE IF EXISTS `{self.test_engine.url.database}`'))

    def create_test_database(self) -> None:
        self.check()
        self.connection.execute(sa.text(f'CREATE DATABASE {self.test_engine.url.database};'))

    def test_database_exists(self) -> bool:
        self.check()
        return (
            self.connection.scalar(
                sa.text('SELECT 1 FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = :dbname'),
                parameters={'dbname': self.test_engine.url.database},
            )
            is not None
        )

    def check(self):
        super().check()
        assert getattr(self, 'connection', None) is not None, 'Connection has not been created yet. Use calls inside context manager'
