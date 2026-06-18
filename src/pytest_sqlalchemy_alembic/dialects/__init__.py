from .base import BaseDatabaseManager
from .mariadb import MariaDBManager
from .postgresql import PostgresqlManager
from .sqlite import SqliteManager

__all__ = ['DATABASE_MANAGERS', 'BaseDatabaseManager']

DATABASE_MANAGERS: dict[str, type[BaseDatabaseManager]] = {
    'postgresql': PostgresqlManager,
    'postgresql+psycopg': PostgresqlManager,
    'postgresql+psycopg2': PostgresqlManager,
    'postgresql+pg8000': PostgresqlManager,
    'postgresql+psycopg2cffi': PostgresqlManager,
    'postgresql+asyncpg': PostgresqlManager,
    'sqlite': SqliteManager,
    'sqlite+pysqlite': SqliteManager,
    'sqlite+pysqlcipher': SqliteManager,
    'sqlite+aiosqlite': SqliteManager,
    'mariadb': MariaDBManager,
    'mariadb+mysqldb': MariaDBManager,
    'mariadb+pymysql': MariaDBManager,
    'mariadb+mariadbconnector': MariaDBManager,
    'mariadb+cymysql': MariaDBManager,
    'mariadb+asyncmy': MariaDBManager,
    'mariadb+aiomysql': MariaDBManager,
    'mysql': MariaDBManager,
    'mysql+mysqldb': MariaDBManager,
    'mysql+pymysql': MariaDBManager,
    'mysql+mysqlconnector': MariaDBManager,
    'mysql+cymysql': MariaDBManager,
    'mysql+asyncmy': MariaDBManager,
    'mysql+aiomysql': MariaDBManager,
}
