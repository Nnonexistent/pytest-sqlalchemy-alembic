from uuid import uuid4

from example_project.main import create_user
from example_project.orm import User

from ..config import SessionLocal


def test_create_user():
    name = str(uuid4())
    email = f"{uuid4}@example.com"

    db = SessionLocal()
    create_user(db, name, email)
    db.close()

    db = SessionLocal()
    user = db.query(User).where(User.username == name).one_or_none()
    assert user is not None
    assert user.username == name
    assert user.email == email
    db.close()
