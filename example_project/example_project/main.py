from sqlalchemy.orm import Session

from .db import db_ctx
from .models import User


def create_user(db: Session, username: str, email: str) -> User:
    user = User(username=username, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


if __name__ == '__main__':
    with db_ctx() as db:
        user = create_user(db, 'john_doe', 'john@example.com')
