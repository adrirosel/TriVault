"""Pytest configuration and isolated database fixtures."""

import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv

# Load local backend/.env if present (gitignored) without overriding explicit CI env vars.
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

# Provide deterministic fallback defaults only when env vars and .env are absent (e.g. CI).
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault(
    "SECRET_KEY",
    "ephemeral-ci-test-secret-key-at-least-thirty-two-bytes",
)
os.environ.setdefault(
    "DATABASE_URL",
    "mysql+pymysql://ci_test_user:ci_test_password@127.0.0.1:3307/trivault_test",
)
os.environ.setdefault(
    "TEST_DATABASE_URL",
    "mysql+pymysql://ci_test_user:ci_test_password@127.0.0.1:3307/trivault_test",
)
os.environ.setdefault("ALLOWED_ORIGINS", '["http://localhost:5173"]')

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.core.database import build_engine
from app.main import app
from app.models import Base


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    """Create schema once in the dedicated test database and tear it down afterwards."""
    settings = get_settings()
    database_url = settings.TEST_DATABASE_URL or settings.DATABASE_URL
    engine = build_engine(database_url)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Generator[Session, None, None]:
    """Run each test inside a transaction rolled back at teardown."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient wired to the isolated test session."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
