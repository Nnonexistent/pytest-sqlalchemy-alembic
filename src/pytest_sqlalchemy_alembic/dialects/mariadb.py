from contextlib import suppress

import sqlalchemy as sa
from sqlalchemy.exc import OperationalError

from .base import BaseDatabaseManager


class MariaDBManager(BaseDatabaseManager):
    def make_test_engine_url(self, worker_id: str) -> sa.URL:
        url = self.engine.url
        return url.set(database=f'{url.database}_test_{worker_id}')

    def drop_test_database(self, connection: sa.Connection) -> None:
        self.check()
        connection_ids = connection.execute(
            sa.text("""
                SELECT id FROM information_schema.processlist
                WHERE db = :db_name AND id != CONNECTION_ID()
            """),
            {'db_name': self.test_engine.url.database},
        )

        for cid in [row[0] for row in connection_ids.fetchall()]:
            with suppress(OperationalError):  # connection may already be gone
                connection.execute(sa.text(f'KILL CONNECTION {cid}'))

        connection.execute(sa.text(f'DROP DATABASE IF EXISTS `{self.test_engine.url.database}`'))

    def create_test_database(self, connection: sa.Connection) -> None:
        self.check()
        connection.execute(sa.text(f'CREATE DATABASE {self.test_engine.url.database};'))

    def test_database_exists(self, connection: sa.Connection) -> bool:
        self.check()
        return (
            connection.scalar(
                sa.text('SELECT 1 FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = :dbname'),
                parameters={'dbname': self.test_engine.url.database},
            )
            is not None
        )
