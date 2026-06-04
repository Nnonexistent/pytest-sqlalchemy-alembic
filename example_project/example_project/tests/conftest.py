import pytest


@pytest.fixture
def db():
    from example_project.db import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
