from __future__ import annotations

import logging

import pytest
from alembic.command import upgrade as alembic_upgrade
from alembic.config import CommandLine as AlembicCli
from alembic.config import Config as AlembicConfig
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

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


@pytest.fixture(autouse=True, scope="session")
def db_setup(request: pytest.FixtureRequest, worker_id: str):
    # TODO: Make sure all ORM models are imported

    create_db = request.config.getvalue("create_db")
    nomigrations = request.config.getvalue("nomigrations")

    original_db_url = make_url(TODO_DATABASE_DSN)
    test_db_url = original_db_url.set(database=f"{original_db_url.database}_test_{worker_id}")
    test_engine = create_engine(test_db_url, **TODO_OVERRIDABLE_KWARGS)

    autocommit_connection = ORIGINAL_ENGINE.connect().execution_options(isolation_level="AUTOCOMMIT")
    if create_db:
        _logger.info("Recreating database: %s", test_db_url.database)
        autocommit_connection.execute(text(f"DROP DATABASE IF EXISTS {test_db_url.database} WITH (FORCE);"))
        autocommit_connection.execute(text(f"CREATE DATABASE {test_db_url.database} OWNER {test_db_url.username};"))
    else:
        res = autocommit_connection.execute(
            text("SELECT 1 FROM pg_catalog.pg_database WHERE datname = :dbname"),
            parameters={"dbname": test_db_url.database},
        )
        if res.scalar_one_or_none() is None:
            _logger.info("Creating database: %s", test_db_url.database)
            autocommit_connection.execute(text(f"CREATE DATABASE {test_db_url.database} OWNER {test_db_url.username};"))
        else:
            _logger.info("Reusing database: %s", test_db_url.database)

    autocommit_connection.close()

    Base = ...  # TODO: configurable import of base class for sqlalchemy ORM models
    if nomigrations:
        _logger.info("Creating tables for %s", test_db_url.database)
        Base.metadata.create_all(bind=test_engine)
    else:
        _logger.info("Migrating database %s", test_db_url.database)
        options = AlembicCli().parser.parse_args(["upgrade", "head"])
        alembic_config = AlembicConfig(
            file_=options.config,
            ini_section=options.name,
            cmd_opts=options,
        )
        alembic_config.set_main_option("sqlalchemy.url", test_db_url.render_as_string(hide_password=False))
        alembic_upgrade(alembic_config, "head")

    session_maker_instance = ...  # TODO: configurable import of sessionmaker instance
    session_maker_instance.configure(bind=test_engine)

    yield test_engine

    session_maker_instance.configure(bind=ORIGINAL_ENGINE)
