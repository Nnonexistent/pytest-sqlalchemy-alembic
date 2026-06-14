from .base import BaseDatabaseManager
from .postgresql import PostgresqlManager
from .sqlite import SqliteManager

__all__ = ['DATABASE_MANAGERS', 'BaseDatabaseManager']


DATABASE_MANAGERS: dict[str, type[BaseDatabaseManager]] = {
    'postgresql': PostgresqlManager,
    'postgresql+psycopg': PostgresqlManager,
    'postgresql+psycopg2': PostgresqlManager,
    'postgresql+pg8000': PostgresqlManager,
    'postgresql+psycopg2cffi': PostgresqlManager,
    'sqlite': SqliteManager,
    'sqlite+pysqlite': SqliteManager,
    'sqlite+pysqlcipher': SqliteManager,
}
