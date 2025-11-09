from collections.abc import Sequence
from importlib import import_module
from typing import Any

from alembic.config import CommandLine as AlembicCommandLine
from alembic.config import Config as AlembicConfig
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from alembic.util import load_python_file
from sqlalchemy import Engine, MetaData, create_engine


def import_string(import_path: str) -> Any:
    assert ":" in import_path

    module_path, obj_name = import_path.split(":", 1)
    module = import_module(module_path)

    return getattr(module, obj_name)


def clone_engine(engine: Engine, new_url: str, **kwargs) -> Engine:
    return create_engine(
        new_url,
        execution_options=engine._execution_options,
        echo=engine.echo,
        logging_name=engine.logging_name,
        hide_parameters=engine.hide_parameters,
        **kwargs,
    )


def alembic_upgrade(url: str) -> None:
    command_line = AlembicCommandLine()
    options = command_line.parser.parse_args(["upgrade", "head"])

    toml, ini = command_line._inis_from_config(options)
    cfg = AlembicConfig(
        file_=ini,
        toml_file=toml,
        ini_section=options.name,
        cmd_opts=options,
    )
    cfg.set_main_option("sqlalchemy.url", url)
    command_line.run_cmd(cfg, options)


def get_alembic_target_metadata() -> Sequence[MetaData]:
    command_line = AlembicCommandLine()
    options = command_line.parser.parse_args(["current"])
    toml, ini = command_line._inis_from_config(options)
    alembic_config = AlembicConfig(
        file_=ini,
        toml_file=toml,
        ini_section=options.name,
        cmd_opts=options,
    )
    script = ScriptDirectory.from_config(alembic_config)

    with EnvironmentContext(alembic_config, script, fn=lambda rev, context: [], dont_mutate=True):
        env_module = load_python_file(script.dir, "env.py")
    metadata = env_module.target_metadata

    if hasattr(metadata, "__iter__"):
        return metadata
    else:
        return [metadata]
