from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine

from .base import BaseDatabaseManager


class SqliteManager(BaseDatabaseManager):
    def create_test_engine(self, worker_id: str, engine_kwargs: dict[str, Any]) -> Engine:
        if self._is_in_memory():
            test_db_url = self.engine.url
        else:
            assert self.engine.url.database is not None
            file_path = Path(self.engine.url.database)
            test_db_url = self.engine.url.set(database=f'{file_path.stem}_test_{worker_id}{file_path.suffix}')
        self.test_engine = create_engine(test_db_url, **engine_kwargs)
        return self.test_engine

    def drop_test_database(self) -> None:
        self.check()
        if self._is_in_memory():
            return

        assert self.test_engine.url.database is not None
        Path(self.test_engine.url.database).unlink(missing_ok=True)

    def create_test_database(self) -> None:
        pass

    def test_database_exists(self) -> bool:
        self.check()
        if self._is_in_memory():
            return True

        assert self.test_engine.url.database is not None
        return Path(self.test_engine.url.database).exists()

    def _is_in_memory(self) -> bool:
        # We're checking here BASE database url, but it will be the same for the test engine database
        return not self.engine.url.database or self.engine.url.database == ':memory:'
