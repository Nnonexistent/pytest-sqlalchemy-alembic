from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal, TypeAlias, TypeGuard

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from typing_extensions import Self

from .dialects import DATABASE_MANAGERS, BaseDatabaseManager
from .utils import TypeCheckDataclass, get_alembic_target_metadata, import_string

AnySessionMaker: TypeAlias = async_sessionmaker[AsyncSession] | sessionmaker[Session]
AnyEngine: TypeAlias = AsyncEngine | sa.Engine


class ConfigValidationError(ValueError):
    pass


class PluginConfig:
    __slots__ = ('database_manager', 'engine', 'engine_kwargs', 'metadata', 'scope', 'session_maker')

    def __init__(
        self,
        session_maker: AnySessionMaker | None,
        engine_kwargs: dict[str, Any],
        engine: AnyEngine,
        database_manager: type[BaseDatabaseManager],
        metadata: Sequence[sa.MetaData],
        scope: Literal['session', 'function'],
    ):
        self.session_maker = session_maker
        self.engine_kwargs = engine_kwargs
        self.engine = engine
        self.database_manager = database_manager
        self.metadata = metadata
        self.scope = scope

    @classmethod
    def build_list(cls, config: pytest.Config) -> list[Self]:
        raw_value: list[str] | list[Any] = config.getini('sqlalchemy_alembic_configs')
        configs = []
        for raw_entry in raw_value:
            if (entry := IniEntry.parse(raw_entry)) is not None:
                configs.append(cls.build(ini_entry=entry))
        return configs

    @classmethod
    def build(
        cls,
        ini_entry: IniEntry | None = None,
        session_maker: AnySessionMaker | None = None,
        metadata: sa.MetaData | Sequence[sa.MetaData] | None = None,
        engine: AnyEngine | None = None,
        engine_url: str | None = None,
        engine_kwargs: dict[str, Any] | None = None,
        orm_loader: Callable[[], None] | None = None,
        scope: Literal['session', 'function'] | None = None,
    ) -> Self:
        if ini_entry is None:
            ini_entry = IniEntry()

        session_maker = cls._parse_session_maker(session_maker, ini_entry.session_maker)
        engine_kwargs = cls._parse_engine_kwargs(engine_kwargs, ini_entry.engine_kwargs)
        engine = cls._parse_engine(engine, ini_entry.engine, engine_url, ini_entry.engine_url, engine_kwargs, session_maker)
        metadata = cls._parse_metadata(metadata, ini_entry.metadata)
        assert ini_entry.scope in ('session', 'function')
        scope = cls._parse_scope(scope, ini_entry.scope)

        if engine.url.drivername not in DATABASE_MANAGERS:
            msg = f'Unsupported database dialect: {engine.url.drivername}'
            raise ConfigValidationError(msg)
        database_manager = DATABASE_MANAGERS[engine.url.drivername]

        cls._load_orm_models(orm_loader, ini_entry.orm_loader)
        return cls(
            session_maker=session_maker,
            engine_kwargs=engine_kwargs,
            engine=engine,
            database_manager=database_manager,
            metadata=metadata,
            scope=scope,
        )

    @classmethod
    def import_from_string(cls, import_path: str) -> Any:
        try:
            return import_string(import_path)
        except ImportError as e:
            msg = f'Error importing {import_path!r}: {e}'
            raise ConfigValidationError(msg) from e

    @classmethod
    def _parse_session_maker(cls, session_maker: AnySessionMaker | None, session_maker_path: str | None) -> AnySessionMaker | None:
        if session_maker is None:
            if session_maker_path is None:
                return None

            if not session_maker_path:
                return None
            session_maker = cls.import_from_string(session_maker_path)

        if not isinstance(session_maker, (sessionmaker, async_sessionmaker)):
            msg = f'`session_maker` must be a sessionmaker or async_sessionmaker, got {type(session_maker).__name__!r}'
            raise ConfigValidationError(msg)

        return session_maker

    @classmethod
    def _parse_engine_kwargs(cls, engine_kwargs: dict[str, Any] | None, engine_kwargs_path: str | None) -> dict[str, Any]:
        if engine_kwargs is None:
            if engine_kwargs_path is None:
                return {}

            if engine_kwargs_path:
                engine_kwargs = cls.import_from_string(engine_kwargs_path)
            else:
                return {}

        if not isinstance(engine_kwargs, dict):
            msg = f'`engine_kwargs` must be a dict, got {type(engine_kwargs).__name__!r}'
            raise ConfigValidationError(msg)
        return engine_kwargs

    @classmethod
    def _parse_engine(
        cls,
        engine: AnyEngine | None,
        engine_path: str | None,
        engine_url: str | None,
        engine_url_from_ini: str | None,
        engine_kwargs: dict[str, Any],
        session_maker: AnySessionMaker | None,
    ) -> AnyEngine:
        new_engine: sa.Engine | AsyncEngine | None = None

        if engine is not None:
            new_engine = engine

        elif engine_path is not None:
            new_engine = cls.import_from_string(engine_path)

        elif engine_url is not None:
            if cls._is_async(engine_url):
                new_engine = create_async_engine(engine_url, **engine_kwargs)
            else:
                new_engine = sa.create_engine(engine_url, **engine_kwargs)

        elif engine_url_from_ini is not None:
            if cls._is_async(engine_url_from_ini):
                new_engine = create_async_engine(engine_url_from_ini, **engine_kwargs)
            else:
                new_engine = sa.create_engine(engine_url_from_ini, **engine_kwargs)

        elif session_maker is not None and isinstance(session_maker.kw['bind'], (sa.Engine, AsyncEngine)):
            new_engine = session_maker.kw['bind']

        else:
            msg = "Couldn't configure engine: missing required config: engine, engine_url or session_maker"
            raise ConfigValidationError(msg)

        if not isinstance(new_engine, AnyEngine):
            msg = f'`engine` must be an Engine or AsyncEngine, got {type(new_engine).__name__!r}'
            raise ConfigValidationError(msg)
        return new_engine

    @classmethod
    def _parse_metadata(cls, metadata: sa.MetaData | Sequence[sa.MetaData] | None, metadata_path: str | None) -> Sequence[sa.MetaData]:
        if metadata is None:
            if metadata_path is None:
                metadata = get_alembic_target_metadata()
            else:
                metadata = cls.import_from_string(metadata_path)

        metadata_list: Sequence[Any]
        if not isinstance(metadata, Sequence):
            metadata_list = [metadata]
        else:
            metadata_list = metadata

        for one_metadata in metadata_list:
            if not isinstance(one_metadata, sa.MetaData):
                msg = f'`metadata` must contain metadata instance(s), got {type(one_metadata).__name__!r}'
                raise ConfigValidationError(msg)
        return metadata_list

    @classmethod
    def _parse_scope(
        cls,
        scope: Literal['session', 'function'] | None,
        scope_from_ini: str,
    ) -> Literal['session', 'function']:
        if scope is None:
            assert cls._validate_scope(scope_from_ini)
            scope = scope_from_ini
        if scope not in ('session', 'function'):
            msg = f'`scope` must be one of "session" or "function", got {scope!r}'
            raise ConfigValidationError(msg)
        return scope

    @classmethod
    def _load_orm_models(cls, orm_loader: Callable[[], Any] | None, orm_loader_path: str | None) -> None:
        if orm_loader is not None:
            orm_loader()

        elif orm_loader_path is not None:
            orm_loader = cls.import_from_string(orm_loader_path)
            if callable(orm_loader):
                orm_loader()

    @classmethod
    def _is_async(cls, url: str) -> bool:
        return sa.make_url(url).get_dialect().is_async

    @classmethod
    def _validate_scope(cls, scope: str) -> TypeGuard[Literal['session', 'function']]:
        return scope in ('session', 'function')


@dataclass(slots=True)
class IniEntry(TypeCheckDataclass):
    session_maker: str | None = None
    engine: str | None = None
    engine_url: str | None = None
    engine_kwargs: str | None = None
    orm_loader: str | None = None
    metadata: str | None = None
    scope: str = 'session'
    skip_db_management: bool = False

    def __post_init__(self) -> None:
        if self.scope not in ('session', 'function'):
            msg = f'`scope` must be one of "session" or "function", got {self.scope!r}'
            raise TypeError(msg)

    @classmethod
    def parse(cls, entry: Any) -> Self | None:
        if isinstance(entry, dict):
            try:
                return cls(**entry)
            except TypeError as error:
                msg = f'Invalid configuration entry format: {entry}. Details: {error}'
                raise pytest.UsageError(msg) from error

        elif isinstance(entry, str):
            entry = entry.lstrip()
            assert isinstance(entry, str)

            if not entry or entry.startswith('//'):
                return None

            try:
                evaluated = json.loads(entry)
            except ValueError as error:
                msg = f"Could not parse configuration row: '{entry}'. Details: {error}"
                raise pytest.UsageError(msg) from error

            if not isinstance(evaluated, dict):
                msg = f'Invalid configuration entry format: {entry}. Expected a dictionary, got {type(evaluated).__name__!r}.'
                raise pytest.UsageError(msg)

            try:
                return cls(**evaluated)
            except TypeError as error:
                msg = f'Invalid configuration entry format: {entry}. Details: {error}'
                raise pytest.UsageError(msg) from error

        else:
            msg = f'Invalid configuration entry type: {type(entry).__name__}. Expected dict or str.'
            raise pytest.UsageError(msg)
