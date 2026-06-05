# pytest-sqlalchemy-alembic

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
* `pytest-xdist` >= 3.0 (Optional)


## Supported dialects

> [!WARNING]
> Async engines are not yet supported

| Driver | Status |
| ------ | ------ |
| `postgresql+psycopg` | ✅ Supported
| `postgresql+psycopg2` | ✅ Supported
| `postgresql+pg8000` | ❌
| `postgresql+psycopg2cffi` | ❌
| `postgresql+asyncpg` | ❌
| `mysql+pymysql` | ❌
| `mariadb+pymysql` | ❌
| `sqlite` | ✅ Supported

> [!NOTE]
> If you need an implementation for your particular SQLAlchemy driver, please consider contributing to this project.


## Installation

```bash
pip install pytest-sqlalchemy-alembic
```


## Minimal configuration

Configuration could be done in `pyproject.toml`, `pytest.ini` or via pytest fixture. At least `session_maker`, `engine` or `engine_url` should be specified.


### `pyproject.toml`

```toml
[tool.pytest.ini_options]
sqlalchemy_session_maker = "example_project.db:SessionLocal"
```

### `pytest.ini`

```ini
[pytest]
sqlalchemy_session_maker = example_project.db:SessionLocal
```

### `conftest.py`

```python
import pytest
from pytest_sqlalchemy_alembic.config import PluginConfig
from example_project.db import SessionLocal

@pytest.fixture(scope='session')
def sqlalchemy_alembic_plugin_config() -> PluginConfig:
    return PluginConfig.build(session_maker=SessionLocal)
```


## Full list of configuration options

### Config file options

| Option | Description
| ------ | -----------
| `sqlalchemy_session_maker` | Import path to a sessionmaker instance
| `sqlalchemy_metadata`      | Import path to SQLAlchemy metadata. Usually `metadata` attribute of a declarative base class. <br>Used for non-alembic database schema population based on metadata. Metadata is extracted from the alembic config if this option is empty
| `sqlalchemy_engine`        | Import path to SQLAlchemy engine instance. <br>If empty, created using `engine_url` and `engine_kwargs` or extracted from the sessionmaker instance
| `sqlalchemy_engine_url`    | SQLAlchemy engine URL. Extracted from `engine` if empty
| `sqlalchemy_engine_kwargs` | Import path to a dict containing engine kwargs
| `sqlalchemy_orm_loader`    | Import path to module or callable that loads all ORM necessary models


### Fixture override options

Arguments of `PluginConfig.build` class method to use in the `sqlalchemy_alembic_plugin_config` fixture.

| Argument | Type | Description
| -------- | ---- | -----------
| `session_maker` | `sa.orm.sessionmaker[Session]` | Instance of a sessionmaker
| `metadata`      | `sa.MetaData | Sequence[sa.MetaData]` | SQLAlchemy metadata
| `engine`        | `sa.Engine` | Sqlalchemy engine instance
| `engine_url`    | `str` | SQLAlchemy engine URL
| `engine_kwargs` | `dict[str, Any]` | `dict` with kwargs for `sa.create_engine` function. E.g. `{'json_serializer': my_json_serializer}`
| `orm_loader`    | `Callable[[], Any]` | Callable, that will load all ORM necessary models


## Combining file configuration and fixture override

In this example `session_maker` will be defined in `pyproject.toml` and `metadata` will be directly imported in the `conftest.py`.

```toml
# pyproject.toml
[tool.pytest.ini_options]
sqlalchemy_session_maker = "example_project.db:SessionLocal"
```

```python
# conftest.py
import pytest
from pytest_sqlalchemy_alembic.config import PluginConfig
from example_project.models import Base

@pytest.fixture(scope='session')
def sqlalchemy_alembic_plugin_config(pytestconfig: pytest.Config) -> PluginConfig:
    return PluginConfig.build(config=pytestconfig, metadata=Base.metadata)
```


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

| Flag | Description |
| ---- | ----------- |
| `--createdb` / `--create-db` | Drop and recreate the test database before the session
| `--nomigrations` / `--no-migrations` | Skip Alembic migrations and use `metadata.create_all()` instead


## Fixtures

| Fixture | Scope | Output | Description |
| ------- | ----- | ------ | ----------- |
| `sqlalchemy_alembic_setup` | session | Test SQLAlchemy engine | Autouse fixture that creates and migrates the test database and rebinds the configured sessionmaker
| `sqlalchemy_alembic_plugin_config` | session | This plugin's config | Extension point to override config values from python context
