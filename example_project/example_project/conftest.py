import pytest
from sqlalchemy.orm import sessionmaker

from .config import SessionLocal


@pytest.fixture(scope="session")
def sqlalchemy_sessionmaker() -> sessionmaker:
    return SessionLocal
