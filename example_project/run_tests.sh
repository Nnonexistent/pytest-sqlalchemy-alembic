#!/bin/sh
PYTHONPATH=.. pytest --tb=native -s -p pytest_sqlalchemy_alembic "$@"
PYTHONPATH=.. pytest --override-dialect=mysql --tb=native -s -p pytest_sqlalchemy_alembic "$@"
PYTHONPATH=.. pytest --override-dialect=postgresql --tb=native -s -p pytest_sqlalchemy_alembic "$@"
