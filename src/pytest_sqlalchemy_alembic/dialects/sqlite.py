from pathlib import Path

import sqlalchemy as sa

from .base import BaseDatabaseManager


class SqliteManager(BaseDatabaseManager):
    def make_test_engine_url(self, worker_id: str) -> sa.URL:
        if self._is_in_memory():
            return self.engine.url
        assert self.engine.url.database is not None
        file_path = Path(self.engine.url.database)
        return self.engine.url.set(database=f'{file_path.stem}_test_{worker_id}{file_path.suffix}')

    def drop_test_database(self, connection: sa.Connection) -> None:
        self.check()
        if self._is_in_memory():
            return

        assert self.test_engine.url.database is not None
        Path(self.test_engine.url.database).unlink(missing_ok=True)

    def create_test_database(self, connection: sa.Connection) -> None:
        pass

    def test_database_exists(self, connection: sa.Connection) -> bool:
        self.check()
        if self._is_in_memory():
            return True

        assert self.test_engine.url.database is not None
        return Path(self.test_engine.url.database).exists()

    def _is_in_memory(self) -> bool:
        # We're checking here BASE database url, but it will be the same for the test engine database
        return not self.engine.url.database or self.engine.url.database == ':memory:'
