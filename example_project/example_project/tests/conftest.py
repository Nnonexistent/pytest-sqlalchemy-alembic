from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session


@pytest.fixture
def db() -> Generator[Session]:
    from example_project.db import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
