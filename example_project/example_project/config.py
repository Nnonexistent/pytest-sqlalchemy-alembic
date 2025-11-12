from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

_DATABASE_URLS = {
    "mysql": "mysql:///psa_example_database",
    "sqlite": "sqlite:///./database.db",
    "postgresql": "postgresql:///psa_example_database"
}

DATABASE_URL = _DATABASE_URLS["postgresql"]

connect_kw = {}
if "sqlite" in DATABASE_URL:
    connect_kw["check_same_thread"] = False

# Create engine
engine = create_engine(DATABASE_URL, connect_args=connect_kw)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class for declarative models
class Base(DeclarativeBase):
    pass
