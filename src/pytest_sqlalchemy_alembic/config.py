from collections.abc import Callable, Sequence
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker
from typing_extensions import Self

from .dialects import DATABASE_MANAGERS, BaseDatabaseManager
from .utils import get_alembic_target_metadata, import_string


class ConfigValidationError(ValueError):
    pass


class PluginConfig:
    __slots__ = ('database_manager', 'engine', 'engine_kwargs', 'metadata', 'session_maker')

    def __init__(
        self,
        session_maker: sessionmaker[Session] | None,
        engine_kwargs: dict[str, Any],
        engine: sa.engine.Engine,
        database_manager: type[BaseDatabaseManager],
        metadata: Sequence[sa.MetaData],
    ):
        self.session_maker = session_maker
        self.engine_kwargs = engine_kwargs
        self.engine = engine
        self.database_manager = database_manager
        self.metadata = metadata

    @classmethod
    def build(
        cls,
        config: pytest.Config | None = None,
        session_maker: sessionmaker[Session] | None = None,
        metadata: sa.MetaData | Sequence[sa.MetaData] | None = None,
        engine: sa.Engine | None = None,
        engine_url: str | None = None,
        engine_kwargs: dict[str, Any] | None = None,
        orm_loader: Callable[[], None] | None = None,
    ) -> Self:
        session_maker = cls._parse_session_maker(config, session_maker)
        engine_kwargs = cls._parse_engine_kwargs(config, engine_kwargs)
        engine = cls._parse_engine(config, engine, engine_url, engine_kwargs, session_maker)
        metadata = cls._parse_metadata(config, metadata)
        cls._load_orm_models(config, orm_loader)

        if engine.url.drivername not in DATABASE_MANAGERS:
            msg = f'Unsupported database dialect: {engine.url.drivername}'
            raise ConfigValidationError(msg)
        database_manager = DATABASE_MANAGERS[engine.url.drivername]

        return cls(
            session_maker=session_maker,
            engine_kwargs=engine_kwargs,
            engine=engine,
            database_manager=database_manager,
            metadata=metadata,
        )

    @classmethod
    def import_from_string(cls, import_path: str) -> Any:
        try:
            return import_string(import_path)
        except ImportError as e:
            msg = f'Error importing {import_path!r}: {e}'
            raise ConfigValidationError(msg) from e

    @classmethod
    def _parse_session_maker(cls, config: pytest.Config | None, session_maker: sessionmaker[Session] | None) -> sessionmaker[Session] | None:
        if session_maker is None:
            if config is None:
                return None

            session_maker_path = config.getini('sqlalchemy_session_maker')
            if not session_maker_path:
                return None
            session_maker = cls.import_from_string(session_maker_path)

        if not isinstance(session_maker, sessionmaker):
            msg = f'`sqlalchemy_session_maker` must be a sessionmaker, got {type(session_maker).__name__!r}'
            raise ConfigValidationError(msg)

        return session_maker

    @classmethod
    def _parse_engine_kwargs(cls, config: pytest.Config | None, engine_kwargs: dict[str, Any] | None) -> dict[str, Any]:
        if engine_kwargs is None:
            if config is None:
                return {}

            engine_kwargs_path = config.getini('sqlalchemy_engine_kwargs')
            if engine_kwargs_path:
                engine_kwargs = cls.import_from_string(engine_kwargs_path)
            else:
                return {}

        if not isinstance(engine_kwargs, dict):
            msg = f'`sqlalchemy_engine_kwargs` must be a dict, got {type(engine_kwargs).__name__!r}'
            raise ConfigValidationError(msg)
        return engine_kwargs

    @classmethod
    def _parse_engine(
        cls,
        config: pytest.Config | None,
        engine: sa.Engine | None,
        engine_url: str | None,
        engine_kwargs: dict[str, Any],
        session_maker: sessionmaker[Session] | None,
    ) -> sa.Engine:
        if engine is None:
            if config is not None and (engine_path := config.getini('sqlalchemy_engine')):
                engine = cls.import_from_string(engine_path)

            elif engine_url is not None:
                engine = sa.create_engine(engine_url, **engine_kwargs)

            elif config is not None and (engine_url_str := config.getini('sqlalchemy_engine_url')):
                engine = sa.create_engine(engine_url_str, **engine_kwargs)

            elif session_maker is not None and isinstance(session_maker.kw['bind'], sa.Engine):
                engine = session_maker.kw['bind']

            else:
                msg = "Couldn't configure engine: missing required config: sqlalchemy_engine, sqlalchemy_engine_url or sqlalchemy_session_maker"
                raise ConfigValidationError(msg)

        if not isinstance(engine, sa.Engine):
            msg = f'`sqlalchemy_engine` must be an Engine, got {type(engine).__name__!r}'
            raise ConfigValidationError(msg)
        return engine

    @classmethod
    def _parse_metadata(cls, config: pytest.Config | None, metadata: sa.MetaData | Sequence[sa.MetaData] | None) -> Sequence[sa.MetaData]:
        if metadata is None:
            if config is None:
                return get_alembic_target_metadata()

            metadata_path = config.getini('sqlalchemy_metadata')
            if not metadata_path:
                return get_alembic_target_metadata()
            metadata = cls.import_from_string(metadata_path)

        metadata_list: Sequence[Any]
        if not isinstance(metadata, Sequence):
            metadata_list = [metadata]
        else:
            metadata_list = metadata

        for one_metadata in metadata_list:
            if not isinstance(one_metadata, sa.MetaData):
                msg = f'`sqlalchemy_metadata` must contain metadata instance(s), got {type(one_metadata).__name__!r}'
                raise ConfigValidationError(msg)
        return metadata_list

    @classmethod
    def _load_orm_models(cls, config: pytest.Config | None, orm_loader: Callable | None) -> None:
        if orm_loader is not None:
            orm_loader()

        elif config is not None and (orm_loader_path := config.getini('sqlalchemy_orm_loader')):
            orm_loader = cls.import_from_string(orm_loader_path)
            if callable(orm_loader):
                orm_loader()
