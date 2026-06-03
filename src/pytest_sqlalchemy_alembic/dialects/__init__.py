from pytest_sqlalchemy_alembic.dialects.sqlite import SqliteBackend

from .base import DialectBackend
from .postgresql_psycopg import PostgresqlPsycopgBackend

__all__ = ['DIALECT_BACKENDS', 'DialectBackend']


DIALECT_BACKENDS = {
    'postgresql+psycopg': PostgresqlPsycopgBackend,
    'postgresql+psycopg2': PostgresqlPsycopgBackend,
    'sqlite': SqliteBackend,
}
