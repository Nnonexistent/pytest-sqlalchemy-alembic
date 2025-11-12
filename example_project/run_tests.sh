#!/bin/sh
PYTHONPATH=.. pytest --tb=native -s -p pytest_sqlalchemy_alembic "$@"
