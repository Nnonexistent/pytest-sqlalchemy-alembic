import pytest

pytest_plugins = ['pytester']


def test_plugin_happy_path(pytester: pytest.Pytester) -> None:
    filepath = pytester.makepyfile(
        """
        import sqlalchemy as sa
        from sqlalchemy.orm import sessionmaker, DeclarativeBase

        engine = sa.create_engine('sqlite:///:memory:')
        SessionLocal = sessionmaker(engine)

        class Base(DeclarativeBase):
            pass

        def test_db():
            with SessionLocal() as db:
                assert db.scalar(sa.text('select 1')) == 1
        """
    )
    module_name = filepath.name.removesuffix('.py')
    pytester.makeini(
        f"""
        [pytest]
        sqlalchemy_session_maker = {module_name}:SessionLocal
        sqlalchemy_declarative_base = {module_name}:Base
        """
    )

    result = pytester.runpytest_subprocess('--nomigrations')

    result.assert_outcomes(errors=0, passed=1)


def test_plugin_load_reports_missing_required_sqlalchemy_config(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_unconfigured():
            pass
        """
    )

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(
        [
            '*Missing required config: sqlalchemy_session_maker*',
        ]
    )
