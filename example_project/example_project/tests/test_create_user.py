from uuid import uuid4

from sqlalchemy.orm import Session


def test_create_user(db: Session):
    from example_project.main import create_user, db_ctx
    from example_project.orm import User

    name = str(uuid4())
    email = f"{uuid4}@example.com"

    with db_ctx() as app_db:
        create_user(app_db, name, email)

    user = db.query(User).where(User.username == name).one_or_none()
    assert user is not None
    assert user.username == name
    assert user.email == email
