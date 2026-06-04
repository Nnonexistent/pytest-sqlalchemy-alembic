import abc
from typing import Any

from sqlalchemy import Engine
from typing_extensions import Self


class BaseDatabaseManager(abc.ABC):
    test_engine: Engine

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

    @abc.abstractmethod
    def create_test_engine(self, worker_id: str, engine_kwargs: dict[str, Any]) -> Engine:
        raise NotImplementedError

    @abc.abstractmethod
    def drop_test_database(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def create_test_database(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def test_database_exists(self) -> bool:
        raise NotImplementedError()

    def check(self) -> None:
        assert getattr(self, 'test_engine', None) is not None, 'Test engine has not been created yet. Call `create_test_engine` first.'


class BaseConcreteManager(BaseDatabaseManager):
    test_engine: Engine
