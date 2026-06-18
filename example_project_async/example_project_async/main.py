from sqlalchemy.ext.asyncio import AsyncSession

from .db import db_ctx
from .models import User


async def create_user(db: AsyncSession, username: str, email: str) -> User:
    user = User(username=username, email=email)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def async_main() -> None:
    async with db_ctx() as db:
        await create_user(db, 'john_doe', 'john@example.com')


def main() -> None:
    import asyncio

    asyncio.run(async_main())


if __name__ == '__main__':
    main()
