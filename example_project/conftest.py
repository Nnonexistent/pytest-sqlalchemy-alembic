def pytest_addoption(parser):
    group = parser.getgroup("sqlalchemy")
    group.addoption(
        "--override-dialect",
        action="store",
        default=None,
        choices=["sqlite", "postgresql", "mysql"],
        help="Force database dialect to use: 'sqlite', 'postgresql', or 'mysql'. No default.",
    )
