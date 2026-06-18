from sqlalchemy import Engine
from sqlalchemy.orm import Session


def test_engine(db: Session) -> None:
    assert isinstance(db.bind, Engine)
    assert db.bind.url.database
    assert 'test' in db.bind.url.database
