from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


def test_engine(db: AsyncSession) -> None:
    assert isinstance(db.bind, AsyncEngine)
    assert db.bind.url.database
    assert 'test' in db.bind.url.database
