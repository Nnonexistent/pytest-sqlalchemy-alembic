# pytest-sqlalchemy-alembic
[![CI](https://github.com/Nnonexistent/pytest-sqlalchemy-alembic/actions/workflows/ci.yml/badge.svg)](https://github.com/Nnonexistent/pytest-sqlalchemy-alembic/actions/workflows/ci.yml)
[![Test all dialects](https://github.com/Nnonexistent/pytest-sqlalchemy-alembic/actions/workflows/test-dialects.yml/badge.svg)](https://github.com/Nnonexistent/pytest-sqlalchemy-alembic/actions/workflows/test-dialects.yml)
<br>
[![PyPI](https://img.shields.io/pypi/v/pytest-sqlalchemy-alembic)](https://pypi.org/project/pytest-sqlalchemy-alembic/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-sqlalchemy-alembic)](https://pypi.org/project/pytest-sqlalchemy-alembic/)
[![PyPI - Format](https://img.shields.io/pypi/format/pytest-sqlalchemy-alembic)](https://pypi.org/project/pytest-sqlalchemy-alembic/)
<br>
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen)](https://github.com/pre-commit/pre-commit)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)


A pytest plugin to manage test databases for SQLAlchemy-based projects.

It automatically provisions a dedicated test database per worker and runs Alembic migrations before your test session. Inspired by [pytest-django](https://pytest-django.readthedocs.io/).


## How it works

1. The plugin creates an SQLAlchemy test engine for each worker process.
2. Test database is created or reused for each test engine. If `--createdb` is given, the test database is dropped beforehand.
3. Database schema is populated via **Alembic** or directly from SQLAlchemy metadata (if `--nomigrations` is given).
4. If configured, the **sessionmaker** instance is rebound to the test engine for the duration of the test session.


## Requirements

* `sqlalchemy` >= 2.0
* `alembic` >= 1.16
* `pytest` >= 8.4

<br>

* `pytest-xdist` >= 3.0 (Optional)
* `pytest-asyncio` >= 1.3.0 (Optional)


## Supported dialects

| Driver                     | Status
| -------------------------- | ------
| `sqlite+pysqlite`          | ✅ Supported
| `sqlite+pysqlcipher`       | ✅ Supported
| `postgresql+psycopg`       | ✅ Supported
| `postgresql+psycopg2`      | ✅ Supported
| `postgresql+pg8000`        | ✅ Supported
| `postgresql+psycopg2cffi`  | ✅ Supported
| `postgresql+asyncpg`       | ✅ Supported
| `mariadb+mysqldb`          | ✅ Supported
| `mariadb+pymysql`          | ✅ Supported
| `mariadb+mariadbconnector` | ✅ Supported
| `mariadb+asyncmy`          | ✅ Supported
| `mariadb+aiomysql`         | ✅ Supported
| `mariadb+cymysql`          | ✅ Supported
| `mysql+mysqldb`            | ✅ Supported
| `mysql+pymysql`            | ✅ Supported
| `mysql+mysqlconnector`     | ✅ Supported
| `mysql+asyncmy`            | ✅ Supported
| `mysql+aiomysql`           | ✅ Supported
| `mysql+cymysql`            | ✅ Supported

> [!NOTE]
> If you need an implementation for your particular SQLAlchemy driver, please consider contributing to this project.


## Installation

```bash
pip install pytest-sqlalchemy-alembic
```
or
```bash
pip install pytest-sqlalchemy-alembic[xdist]  # with pytest-xdist
pip install pytest-sqlalchemy-alembic[async]  # with pytest-asyncio
```


## Minimal configuration

Configuration could be done in `pyproject.toml`, `pytest.ini` or via pytest fixture. At least `session_maker`, `engine` or `engine_url` should be specified.


### `pyproject.toml`

```toml
[tool.pytest.ini_options]
sqlalchemy_alembic_configs = [
  {session_maker = "example_project_async.db:AsyncSessionLocal"},
]
```
In toml, [array of tables](https://toml.io/en/v1.1.0#array) should be used to provide config values

### `pytest.ini`

```ini
[pytest]
sqlalchemy_alembic_configs =
  {"session_maker": "example_project.db:SessionLocal"}
```

In ini each line should be a valid JSON object

### `conftest.py`

```python
import pytest
from pytest_sqlalchemy_alembic.config import PluginConfig
from example_project.db import SessionLocal

@pytest.fixture(scope='session')
def sqlalchemy_alembic_plugin_configs(pytestconfig: pytest.Config) -> list[PluginConfig]:
    return [
        PluginConfig.build(
            session_maker=SessionLocal,
            create_db=pytestconfig.getoption('create_db'),
            no_migrations=pytestconfig.getoption('no_migrations'),
        )
    ]
```


## Full list of configuration options

### Config file options

| Option               | Description
| -------------------- | -----------
| `session_maker`      | Import path to a sessionmaker instance
| `metadata`           | Import path to SQLAlchemy metadata. Usually `metadata` attribute of a declarative base class. <br>Used for non-alembic database schema population based on metadata. Metadata is extracted from the alembic config if this option is empty
| `engine`             | Import path to SQLAlchemy engine instance. <br>If empty, created using `engine_url` and `engine_kwargs` or extracted from the sessionmaker instance
| `engine_url`         | SQLAlchemy engine URL. Extracted from `engine` if empty
| `engine_kwargs`      | Import path to a dict containing engine kwargs
| `orm_loader`         | Import path to module or callable that loads all ORM necessary models
| `scope`              | Defines at which scope test engine should be activated (`session` or `function`). <br> Default: `session`
| `skip_db_management` | If this entry should skip test database management. <br>Useful in case of multiple engines, which use the same database. <br>Default: `false`

### Fixture override options

Arguments of `PluginConfig.build` class method to use in the `sqlalchemy_alembic_plugin_configs` fixture.

| Argument             | Type                                   | Description
| -------------------- | -------------------------------------- | -----------
| `session_maker`      | `sa.orm.sessionmaker[Session]`         | Instance of a sessionmaker
| `metadata`           | `sa.MetaData \| Sequence[sa.MetaData]` | SQLAlchemy metadata
| `engine`             | `sa.Engine`                            | Sqlalchemy engine instance
| `engine_url`         | `str`                                  | SQLAlchemy engine URL
| `engine_kwargs`      | `dict[str, Any]`                       | `dict` with kwargs for `sa.create_engine` function. E.g. `{'json_serializer': my_json_serializer}`
| `orm_loader`         | `Callable[[], Any]`                    | Callable, that will load all ORM necessary models
| `scope`              | `Literal['session', 'function']`       | Defines at which scope test engine should be activated
| `skip_db_management` | `bool`                                 | If this entry should skip test database management. <br>Useful in case of multiple engines, which use the same database


## Usage

When configured, the plugin binds your sessionmaker to the test database automatically.

```python
# services.py
from example_project.db import SessionLocal

def my_service():
    with SessionLocal() as db:
        return db.scalar(...)

# test_services.py
from example_project.services import my_service

def test_my_service():
    my_service()  # <-- test database will be used
```

> [!NOTE]
> Usually you don't need to change any of your code to use test database instead of main one.<br>
> However, if you make database queries outside of your sessionmaker, you need to patch those places manually.


## Pytest run flags

| Flag | Description
| ---- | -----------
| `--createdb` / `--create-db` | Drop and recreate the test database before the session
| `--nomigrations` / `--no-migrations` | Skip Alembic migrations and use `metadata.create_all()` instead


## Fixtures

| Fixture                             | Scope    | Output                           | Description
| ----------------------------------- | -------- | -------------------------------- | -----------
| `sqlalchemy_alembic_plugin_configs` | session  | List of this plugin configs      | Extension point to override config values from python context
| `sqlalchemy_alembic_setup_session`  | session  | Test SQLAlchemy engine           | Session-scoped fixture to set up test database
| `sqlalchemy_alembic_setup_function` | function | Test SQLAlchemy engine or `None` | Function-scoped fixture to set up test database. <br>Used only in case of `engine_scope='function'`
