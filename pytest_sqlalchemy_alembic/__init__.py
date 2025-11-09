from __future__ import annotations

import logging
from collections.abc import Generator

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from .database_manager import DatabaseManager, get_database_manager
from .utils import alembic_upgrade, clone_engine, get_alembic_target_metadata, import_string

_logger = logging.getLogger("test")


def pytest_addoption(parser) -> None:
    group = parser.getgroup("sqlalchemy")
    group.addoption(
        "--create-db",
        action="store_true",
        dest="create_db",
        default=False,
        help="Re-create the database, even if it exists.",
    )
    group.addoption(
        "--nomigrations",
        "--no-migrations",
        action="store_true",
        dest="nomigrations",
        default=False,
        help="Disable alembic migrations on test setup",
    )


@pytest.fixture(scope="session")
def sqlalchemy_sessionmaker_path() -> str:
    return ""


@pytest.fixture(scope="session")
def sqlalchemy_sessionmaker(sqlalchemy_sessionmaker_path: str) -> sessionmaker:
    if not sqlalchemy_sessionmaker_path:
        msg = (
            "You must override the `sqlalchemy_sessionmaker_path` fixture to provide the import path of a sqlalchemy.orm.sessionmaker instance. "
            "Or override `sqlalchemy_sessionmaker` fixture to provide sessionmaker instance itself."
        )
        raise pytest.UsageError(msg)

    session_maker_instance = import_string(sqlalchemy_sessionmaker_path)

    if not isinstance(session_maker_instance, sessionmaker):
        msg = f"{sqlalchemy_sessionmaker_path} is not a sqlalchemy.orm.sessionmaker instance"
        raise pytest.UsageError(msg)

    return session_maker_instance


@pytest.fixture(scope="session")
def sqlalchemy_engine_kwargs() -> dict:
    return {}


@pytest.fixture(scope="session")
def sqlalchemy_database_manager() -> type[DatabaseManager] | None:
    return None


@pytest.fixture(scope="session")
def sqlalchemy_engine(sqlalchemy_sessionmaker: sessionmaker) -> Engine:
    engine = sqlalchemy_sessionmaker.kw["bind"]

    if not isinstance(engine, Engine):
        msg = "The bind of the sessionmaker is not a sqlalchemy Engine instance. You can customize engine discovery in sqlalchemy_engine fixture."
        raise pytest.UsageError(msg)

    return engine


@pytest.fixture(autouse=True, scope="session")
def _db_setup(
    request: pytest.FixtureRequest,
    worker_id: str,
    sqlalchemy_sessionmaker: sessionmaker,
    sqlalchemy_engine: Engine,
    sqlalchemy_engine_kwargs: dict,
    sqlalchemy_database_manager: type[DatabaseManager] | None,
):
    create_db = request.config.getvalue("create_db")
    nomigrations = request.config.getvalue("nomigrations")

    if sqlalchemy_engine.url.database and "." in sqlalchemy_engine.url.database:  # sqlite case to keep file suffix
        name, suffix = sqlalchemy_engine.url.database.rsplit(".", 1)
        new_database_name = f"{name}_test_{worker_id}.{suffix}"
    else:
        new_database_name = f"{sqlalchemy_engine.url.database or 'database'}_test_{worker_id}"
    test_db_url = sqlalchemy_engine.url.set(database=new_database_name)
    test_engine = clone_engine(sqlalchemy_engine, str(test_db_url), **sqlalchemy_engine_kwargs)

    if sqlalchemy_database_manager is None:
        try:
            database_manager_class = get_database_manager(type(sqlalchemy_engine.dialect))
        except ValueError as e:
            msg = f"{e}. Use `sqlalchemy_database_manager` fixture to provide a custom DatabaseManager class."
            raise pytest.UsageError(msg) from e
    else:
        database_manager_class = sqlalchemy_database_manager
    database_manager = database_manager_class(sqlalchemy_engine, test_db_url)

    with database_manager:
        if create_db:
            _logger.info("Recreating database: %s", test_db_url.database)
            database_manager.drop()
            database_manager.create()
        elif database_manager.exists():
            _logger.info("Reusing database: %s", test_db_url.database)
        else:
            _logger.info("Creating database: %s", test_db_url.database)
            database_manager.create()

    target_metadata = get_alembic_target_metadata()
    if nomigrations:
        _logger.info("Creating tables for %s", test_db_url.database)
        for metadata in target_metadata:
            metadata.create_all(bind=test_engine)
    else:
        _logger.info("Migrating database %s", test_db_url.database)
        alembic_upgrade(test_db_url.render_as_string(hide_password=False))

    sqlalchemy_sessionmaker.configure(bind=test_engine)

    yield test_engine

    sqlalchemy_sessionmaker.configure(bind=sqlalchemy_engine)
    test_engine.dispose()


@pytest.fixture
def db(sqlalchemy_sessionmaker: sessionmaker) -> Generator[Session, None, None]:
    db_session = sqlalchemy_sessionmaker()
    try:
        yield db_session
    finally:
        db_session.close()
