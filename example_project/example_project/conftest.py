import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import config


@pytest.fixture(scope="session")
def sqlalchemy_sessionmaker(request: pytest.FixtureRequest) -> sessionmaker:
    dialect_override = request.config.option.override_dialect
    if dialect_override:
        conn_args = {"check_same_thread": False} if dialect_override == "sqlite" else {}
        config.DATABASE_URL = config._DATABASE_URLS[dialect_override]
        config.engine = create_engine(config.DATABASE_URL, connect_args=conn_args)
        config.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=config.engine)
    return config.SessionLocal
