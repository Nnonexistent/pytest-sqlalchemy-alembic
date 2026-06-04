import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from pytest_sqlalchemy_alembic.config import ConfigValidationError, PluginConfig


class Base(DeclarativeBase):
    pass


def test_build_empty_config_requires_engine() -> None:
    with pytest.raises(ConfigValidationError, match="Couldn't configure engine"):
        PluginConfig.build()


def test_build_config_minimal_engine() -> None:
    engine = create_engine('sqlite:///:memory:')
    config = PluginConfig.build(engine=engine)
    assert config.engine == engine
    assert config.session_maker is None
    assert config.engine_kwargs == {}
    assert config.metadata == []


def test_build_config_minimal_session_maker() -> None:
    engine = create_engine('sqlite:///:memory:')
    config = PluginConfig.build(session_maker=sessionmaker(bind=engine))
    assert config.engine == engine
    assert config.session_maker is not None
    assert config.engine_kwargs == {}
    assert config.metadata == []


def test_build_config_minimal_session_maker_requires_engine_bind() -> None:
    with pytest.raises(ConfigValidationError, match="Couldn't configure engine"):
        PluginConfig.build(session_maker=sessionmaker())
