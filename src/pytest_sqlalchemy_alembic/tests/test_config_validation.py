import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from pytest_sqlalchemy_alembic.config import ConfigValidationError, PluginConfig


class Base(DeclarativeBase):
    pass


def test_build_requires_config_or_session_maker() -> None:
    with pytest.raises(ConfigValidationError, match='Missing config or session_maker override'):
        PluginConfig.build()


def test_build_requires_config_or_declarative_base() -> None:
    with pytest.raises(ConfigValidationError, match='Missing config or declarative_base override'):
        PluginConfig.build(session_maker=sessionmaker(), engine=create_engine('sqlite://'))


def test_build_requires_engine_source_when_sessionmaker_unbound() -> None:
    with pytest.raises(ConfigValidationError, match='Missing required config: sqlalchemy_engine or sqlalchemy_engine_url'):
        PluginConfig.build(session_maker=sessionmaker(), declarative_base=Base)
