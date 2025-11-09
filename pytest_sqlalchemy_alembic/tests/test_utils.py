from sqlalchemy import create_engine

from ..utils import clone_engine


def test_clone_engine():
    original_engine = create_engine(
        "sqlite:///original.sqlite",
        echo=True,
        hide_parameters=True,
        logging_name="original_engine",
    )

    new_url = "sqlite:///cloned.sqlite"
    cloned_engine = clone_engine(original_engine, new_url)

    assert str(cloned_engine.url) == new_url
    assert cloned_engine.echo == original_engine.echo
    assert cloned_engine.hide_parameters == original_engine.hide_parameters
    assert cloned_engine.logging_name == original_engine.logging_name
