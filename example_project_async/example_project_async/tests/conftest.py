from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession]:
    from example_project_async.db import AsyncSessionLocal

    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()
