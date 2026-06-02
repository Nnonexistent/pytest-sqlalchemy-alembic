from .base import DialectBackend
from .postgresql_psycopg2 import PostgresqlPsycopg2Backend

__all__ = ['DIALECT_BACKENDS', 'DialectBackend']


DIALECT_BACKENDS = {
    'postgresql+psycopg2': PostgresqlPsycopg2Backend,
}
