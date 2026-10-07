"""Test fixtures: a dedicated PostgreSQL test database and one rolled-back transaction per test."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import URL, Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.enums import UserRole
from app.main import app
from app.models import Base
from tests.factories import auth_headers, create_user

CONNECT_ARGS = {"connect_timeout": settings.database_connect_timeout_seconds}


def _can_connect(url: URL) -> bool:
    probe = create_engine(url, connect_args=CONNECT_ARGS)
    try:
        with probe.connect():
            return True
    except OperationalError:
        return False
    finally:
        probe.dispose()


def _ensure_database_exists(url: URL) -> None:
    """Create the test database through the `postgres` maintenance DB when it is missing."""
    if _can_connect(url):
        return
    maintenance = create_engine(
        url.set(database="postgres"), isolation_level="AUTOCOMMIT", connect_args=CONNECT_ARGS
    )
    try:
        with maintenance.connect() as connection:
            exists = connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": url.database}
            )
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        maintenance.dispose()


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    test_url = settings.test_database_uri
    if test_url.database == settings.database_uri.database:
        pytest.exit(
            "POSTGRES_TEST_DB must differ from the main database: tests drop all tables.",
            returncode=1,
        )
    _ensure_database_exists(test_url)
    test_engine = create_engine(test_url, connect_args=CONNECT_ARGS)
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Iterator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def admin_headers(db_session: Session) -> dict[str, str]:
    return auth_headers(create_user(db_session, "admin", UserRole.ADMIN))


@pytest.fixture
def manager_headers(db_session: Session) -> dict[str, str]:
    return auth_headers(create_user(db_session, "manager", UserRole.MANAGER))


@pytest.fixture
def viewer_headers(db_session: Session) -> dict[str, str]:
    return auth_headers(create_user(db_session, "viewer", UserRole.VIEWER))


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
