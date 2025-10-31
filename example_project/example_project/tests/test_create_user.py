from uuid import uuid4

from example_project.main import create_user, db_ctx
from example_project.orm import User


def test_create_user():
    name = str(uuid4())
    email = f"{uuid4}@example.com"

    with db_ctx() as db:
        create_user(db, name, email)

    with db_ctx() as db:
        user = db.query(User).where(User.username == name).one_or_none()
        assert user is not None
        assert user.username == name
        assert user.email == email
