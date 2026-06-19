import pytest

pytest_plugins = ['pytester']


def test_plugin_happy_path_minimal_sessionmaker(pytester: pytest.Pytester) -> None:
    filepath = pytester.makepyfile(
        """
        import sqlalchemy as sa
        from sqlalchemy.orm import sessionmaker, DeclarativeBase

        engine = sa.create_engine('sqlite:///:memory:')
        SessionLocal = sessionmaker(engine)

        def test_db():
            with SessionLocal() as db:
                assert db.scalar(sa.text('select 1')) == 1
        """
    )
    module_name = filepath.name.removesuffix('.py')
    pytester.makeini(
        f"""
        [pytest]
        sqlalchemy_alembic_configs =
          {{"session_maker": "{module_name}:SessionLocal"}}
        """
    )

    result = pytester.runpytest_subprocess('--nomigrations')

    result.assert_outcomes(errors=0, passed=1)


def test_plugin_happy_path_minimal_engine(pytester: pytest.Pytester) -> None:
    filepath = pytester.makepyfile(
        """
        import sqlalchemy as sa
        from sqlalchemy.orm import sessionmaker, DeclarativeBase

        engine = sa.create_engine('sqlite:///:memory:')

        def test_db():
            with engine.connect() as conn:
                assert conn.execute(sa.text('select 1')).scalar() == 1
        """
    )
    module_name = filepath.name.removesuffix('.py')
    pytester.makeini(
        f"""
        [pytest]
        sqlalchemy_alembic_configs =
          {{"engine": "{module_name}:engine"}}
        """
    )

    result = pytester.runpytest_subprocess('--nomigrations')

    result.assert_outcomes(errors=0, passed=1)


def test_plugin_load_empty_config_ok(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_unconfigured():
            pass
        """
    )

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=1)


def test_plugin_load_reports_missing_required_engine_config(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_under_configured():
            pass
        """
    )
    pytester.makeini(
        """
        [pytest]
        sqlalchemy_alembic_configs =
          {"scope": "session"}
        """
    )

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(["*Couldn't configure engine*"])
