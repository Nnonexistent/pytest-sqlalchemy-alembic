from .base import BaseDatabaseManager
from .postgresql_psycopg import PostgresqlPsycopgManager
from .sqlite import SqliteManager

__all__ = ['DATABASE_MANAGERS', 'BaseDatabaseManager']


DATABASE_MANAGERS: dict[str, type[BaseDatabaseManager]] = {
    'postgresql': PostgresqlPsycopgManager,
    'postgresql+psycopg': PostgresqlPsycopgManager,
    'postgresql+psycopg2': PostgresqlPsycopgManager,
    'sqlite': SqliteManager,
}
