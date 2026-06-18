from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session

from ..db import db_ctx
from ..main import create_user
from ..models import User


def test_create_user(db: Session) -> None:
    name = str(uuid4())
    email = f'{uuid4()}@example.com'

    with db_ctx() as app_db:
        create_user(app_db, name, email)

    user = db.scalar(sa.select(User).where(User.username == name))
    assert user is not None
    assert user.username == name
    assert user.email == email
