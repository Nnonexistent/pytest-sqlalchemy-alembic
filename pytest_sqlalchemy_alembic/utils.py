import pytest


def resolve_worker_id(config: pytest.Config) -> str:
    """Return xdist worker_id when available."""
    xdist_worker_input = getattr(config, 'workerinput', None)
    if isinstance(xdist_worker_input, dict):
        return str(xdist_worker_input.get('workerid', 'unknown'))
    return 'master'
