from typing import Any

from sqlalchemy import Engine


class DialectBackend:
    def __init__(self):
        assert False, 'Non-instantiable class'

    @classmethod
    def create_test_engine(cls, engine: Engine, worker_id: str, engine_kwargs: dict[str, Any]) -> Engine:
        raise NotImplementedError

    @classmethod
    def recreate_test_database(cls, base_engine: Engine, test_engine: Engine) -> None:
        raise NotImplementedError

    @classmethod
    def reuse_or_create_test_database(cls, base_engine: Engine, test_engine: Engine) -> None:
        raise NotImplementedError
