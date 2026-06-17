import pytest


@pytest.fixture
async def db():
    from example_project_async.db import AsyncSessionLocal

    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()
