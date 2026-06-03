from collections.abc import Callable
from importlib import import_module
from typing import Any

import pytest
from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from typing_extensions import Self

from .dialects import DIALECT_BACKENDS, DialectBackend


class ConfigValidationError(ValueError):
    pass


class PluginConfig:
    __slots__ = ('dialect_backend', 'engine', 'engine_kwargs', 'metadata', 'session_maker')

    def __init__(
        self,
        session_maker: sessionmaker[Session],
        engine_kwargs: dict[str, Any],
        engine: Engine,
        dialect_backend: type[DialectBackend],
        metadata: MetaData,
    ):
        self.session_maker = session_maker
        self.engine_kwargs = engine_kwargs
        self.engine = engine
        self.dialect_backend = dialect_backend
        self.metadata = metadata

    @classmethod
    def build(
        cls,
        config: pytest.Config | None = None,
        session_maker: sessionmaker[Session] | None = None,
        declarative_base: type[DeclarativeBase] | None = None,
        engine: Engine | None = None,
        engine_url: str | None = None,
        engine_kwargs: dict[str, Any] | None = None,
        orm_loader: Callable[[], None] | None = None,
    ) -> Self:
        session_maker = cls._parse_session_maker(config, session_maker)
        engine_kwargs = cls._parse_engine_kwargs(config, engine_kwargs)
        engine = cls._parse_engine(config, engine, engine_url, engine_kwargs, session_maker)
        metadata = cls._parse_declarative_base(config, declarative_base).metadata
        cls._load_orm_models(config, orm_loader)

        if engine.url.drivername not in DIALECT_BACKENDS:
            msg = f'Unsupported database dialect: {engine.url.drivername}'
            raise ConfigValidationError(msg)
        dialect_backend = DIALECT_BACKENDS[engine.url.drivername]

        return cls(
            session_maker=session_maker,
            engine_kwargs=engine_kwargs,
            engine=engine,
            dialect_backend=dialect_backend,
            metadata=metadata,
        )

    @classmethod
    def import_from_string(cls, import_path: str) -> Any:
        try:
            if ':' in import_path:
                module_path, obj_name = import_path.split(':', 1)
                module = import_module(module_path)

                return getattr(module, obj_name)
            else:
                return import_module(import_path)

        except (ImportError, AttributeError) as e:
            msg = f'Error importing {import_path!r}: {e}'
            raise ConfigValidationError(msg) from e

    @classmethod
    def _parse_session_maker(cls, config: pytest.Config | None, session_maker: sessionmaker[Session] | None) -> sessionmaker[Session]:
        if session_maker is None:
            if config is None:
                msg = 'Missing config or session_maker override'
                raise ConfigValidationError(msg)

            session_maker_path = config.getini('sqlalchemy_session_maker')
            if not session_maker_path:
                msg = 'Missing required config: sqlalchemy_session_maker'
                raise ConfigValidationError(msg)
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
        engine: Engine | None,
        engine_url: str | None,
        engine_kwargs: dict[str, Any],
        session_maker: sessionmaker[Session],
    ) -> Engine:
        if engine is None:
            if config is not None and (engine_path := config.getini('sqlalchemy_engine')):
                engine = cls.import_from_string(engine_path)

            elif engine_url is not None:
                engine = create_engine(engine_url, **engine_kwargs)

            elif config is not None and (engine_url_str := config.getini('sqlalchemy_engine_url')):
                engine = create_engine(engine_url_str, **engine_kwargs)

            elif isinstance(session_maker.kw['bind'], Engine):
                engine = session_maker.kw['bind']

            else:
                msg = 'Missing required config: sqlalchemy_engine or sqlalchemy_engine_url'
                raise ConfigValidationError(msg)

        if not isinstance(engine, Engine):
            msg = f'`sqlalchemy_engine` must be an Engine, got {type(engine).__name__!r}'
            raise ConfigValidationError(msg)
        return engine

    @classmethod
    def _parse_declarative_base(cls, config: pytest.Config | None, declarative_base: type[DeclarativeBase] | None) -> type[DeclarativeBase]:
        if declarative_base is None:
            if config is None:
                msg = 'Missing config or declarative_base override'
                raise ConfigValidationError(msg)

            declarative_base_path = config.getini('sqlalchemy_declarative_base')
            if not declarative_base_path:
                msg = 'Missing required config: sqlalchemy_declarative_base'
                raise ConfigValidationError(msg)
            declarative_base = cls.import_from_string(declarative_base_path)

        if not isinstance(declarative_base, type) or not issubclass(declarative_base, DeclarativeBase):
            msg = f'`sqlalchemy_declarative_base` must be a subclass of DeclarativeBase, got {type(declarative_base).__name__!r}'
            raise ConfigValidationError(msg)
        return declarative_base

    @classmethod
    def _load_orm_models(cls, config: pytest.Config | None, orm_loader: Callable | None) -> None:
        if orm_loader is not None:
            orm_loader()

        elif config is not None and (orm_loader_path := config.getini('sqlalchemy_orm_loader')):
            orm_loader = cls.import_from_string(orm_loader_path)
            if callable(orm_loader):
                orm_loader()
