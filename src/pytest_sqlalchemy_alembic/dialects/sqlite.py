import logging
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine

from .base import DialectBackend

_logger = logging.getLogger('pytest-sqlalchemy-alembic')


class SqliteBackend(DialectBackend):
    @classmethod
    def create_test_engine(cls, engine: Engine, worker_id: str, engine_kwargs: dict[str, Any]) -> Engine:
        assert engine.url.database is not None
        if engine.url.database == ':memory:':
            test_db_url = engine.url
        else:
            file_path = Path(engine.url.database)
            test_db_url = engine.url.set(database=f'{file_path.stem}_test_{worker_id}{file_path.suffix}')
        return create_engine(test_db_url, **engine_kwargs)

    @classmethod
    def recreate_test_database(cls, base_engine: Engine, test_engine: Engine) -> None:
        assert test_engine.url.database is not None
        Path(test_engine.url.database).unlink(missing_ok=True)

    @classmethod
    def reuse_or_create_test_database(cls, base_engine: Engine, test_engine: Engine) -> None:
        pass
