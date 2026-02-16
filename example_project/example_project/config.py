import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

_DATABASE_URLS = {"mysql": "mysql:///psa_example_database", "sqlite": "sqlite:///./database.db", "postgresql": "postgresql:///psa_example_database"}
DEFAULT_DIALECT = "sqlite"
DATABASE_URL = _DATABASE_URLS[DEFAULT_DIALECT]

if not any(arg.startswith("--override-dialect") for arg in sys.argv):
    conn_args = {"check_same_thread": False} if DEFAULT_DIALECT == "sqlite" else {}
    engine = create_engine(DATABASE_URL, connect_args=conn_args)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class for declarative models
class Base(DeclarativeBase):
    pass
