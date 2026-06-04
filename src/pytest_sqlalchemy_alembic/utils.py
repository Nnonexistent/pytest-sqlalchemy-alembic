from collections.abc import Sequence
from importlib import import_module
from typing import Any

import pytest
import sqlalchemy as sa
from alembic.config import CommandLine as AlembicCommandLine
from alembic.config import Config as AlembicConfig
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from alembic.util import CommandError as AlembicCommandError
from alembic.util import load_python_file


def resolve_worker_id(config: pytest.Config) -> str:
    """Return xdist worker_id when available."""
    xdist_worker_input = getattr(config, 'workerinput', None)
    if isinstance(xdist_worker_input, dict):
        return str(xdist_worker_input.get('workerid', 'unknown'))
    return 'master'


def alembic_upgrade(engine: sa.Engine) -> None:
    url = engine.url.render_as_string(hide_password=False)
    command_line = AlembicCommandLine()
    options = command_line.parser.parse_args(['upgrade', 'head'])

    toml, ini = command_line._inis_from_config(options)
    cfg = AlembicConfig(
        file_=ini,
        toml_file=toml,
        ini_section=options.name,
        cmd_opts=options,
    )
    cfg.set_main_option('sqlalchemy.url', url)
    command_line.run_cmd(cfg, options)


def get_alembic_target_metadata() -> Sequence[sa.MetaData]:
    command_line = AlembicCommandLine()
    options = command_line.parser.parse_args(['current'])
    toml, ini = command_line._inis_from_config(options)
    alembic_config = AlembicConfig(
        file_=ini,
        toml_file=toml,
        ini_section=options.name,
        cmd_opts=options,
    )
    try:
        script = ScriptDirectory.from_config(alembic_config)
    except AlembicCommandError:
        return []

    with EnvironmentContext(alembic_config, script, fn=lambda rev, context: [], dont_mutate=True):
        env_module = load_python_file(script.dir, 'env.py')
    metadata = env_module.target_metadata

    if isinstance(metadata, Sequence):
        return metadata
    else:
        return [metadata]


def import_string(import_path: str) -> Any:
    try:
        if ':' in import_path:
            module_path, obj_name = import_path.split(':', 1)
            module = import_module(module_path)

            obj = module
            for attr in obj_name.split('.'):
                obj = getattr(obj, attr)
            return obj
        else:
            return import_module(import_path)

    except (ImportError, AttributeError) as e:
        msg = f'Error importing {import_path!r}: {e}'
        raise ImportError(msg) from e
