import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from .config import SessionLocal

def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("sqlalchemy")
    group.addoption(
        "--override-dialect",
        action="store",
        default=None,
        choices=["sqlite", "postgresql", "mysql"],
        help="Force database dialect to use: 'sqlite', 'postgresql', or 'mysql'. No default."
    )
    raise AssertionError()

@pytest.fixture(scope="session")
def sqlalchemy_engine(sqlalchemy_engine: Engine, sqlalchemy_sessionmaker: sessionmaker, request: pytest.FixtureRequest) -> Engine:
    dialect = request.config.option.override_dialect
    print(f"\n\nPROJ FIXTURE {dialect}\n\n")
    return sqlalchemy_engine


@pytest.fixture(scope="session")
def sqlalchemy_sessionmaker() -> sessionmaker:
    return SessionLocal
