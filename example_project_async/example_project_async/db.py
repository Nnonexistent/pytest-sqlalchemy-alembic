from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


# Base class for declarative models
class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession]:
    db = AsyncSessionLocal()

    try:
        yield db
    finally:
        await db.close()


@asynccontextmanager
async def db_ctx():
    async for db in get_db():
        yield db
