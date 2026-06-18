from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import db_ctx
from ..main import create_user
from ..models import User


async def test_create_user(db: AsyncSession) -> None:
    name = str(uuid4())
    email = f'{uuid4()}@example.com'

    async with db_ctx() as app_db:
        await create_user(app_db, name, email)

    user = await db.scalar(sa.select(User).where(User.username == name))
    assert user is not None
    assert user.username == name
    assert user.email == email
