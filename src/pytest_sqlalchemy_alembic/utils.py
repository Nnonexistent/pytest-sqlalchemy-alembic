import pytest
import sqlalchemy as sa
from alembic.command import upgrade as alembic_upgrade
from alembic.config import CommandLine as AlembicCli
from alembic.config import Config as AlembicConfig


def resolve_worker_id(config: pytest.Config) -> str:
    """Return xdist worker_id when available."""
    xdist_worker_input = getattr(config, 'workerinput', None)
    if isinstance(xdist_worker_input, dict):
        return str(xdist_worker_input.get('workerid', 'unknown'))
    return 'master'


def run_alembic_upgrade(engine: sa.Engine) -> None:
    options = AlembicCli().parser.parse_args(['upgrade', 'head'])
    alembic_config = AlembicConfig(
        file_=options.config,
        ini_section=options.name,
        cmd_opts=options,
    )
    alembic_config.set_main_option('sqlalchemy.url', engine.url.render_as_string(hide_password=False))
    alembic_upgrade(alembic_config, 'head')
