from contextlib import contextmanager

from sqlalchemy.orm import Session

from .config import SessionLocal
from .orm import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_ctx():
    yield from get_db()


def create_user(db: Session, username: str, email: str) -> User:
    user = User(username=username, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


if __name__ == "__main__":
    # Example: create a user
    db = SessionLocal()
    user = create_user(db, "john_do", "john@example.com")
    db.close()
