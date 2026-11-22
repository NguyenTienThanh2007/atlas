import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

# Point the app at the dedicated test database *before* any app module reads settings.
_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
_test_url = os.environ.get("TEST_DATABASE_URL") or dotenv_values(_ROOT_ENV).get("TEST_DATABASE_URL")
if not _test_url:
    pytest.exit("TEST_DATABASE_URL is not set (env var or repo-root .env).", returncode=2)
# The suite downgrades the schema to empty: refuse anything that isn't clearly a test database.
if not (make_url(_test_url).database or "").endswith("_test"):
    pytest.exit("TEST_DATABASE_URL must name a database ending in '_test'.", returncode=2)
os.environ["DATABASE_URL"] = _test_url
os.environ["APP_ENV"] = "test"

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import Engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import get_engine, get_session  # noqa: E402
from app.ingestion.reference import seed_reference  # noqa: E402
from app.main import create_app  # noqa: E402

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


@pytest.fixture(scope="session")
def engine() -> Engine:
    get_settings.cache_clear()
    get_engine.cache_clear()
    command.upgrade(Config(str(ALEMBIC_INI)), "head")
    return get_engine()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    """A session inside an outer transaction that is always rolled back: tests never leak
    data, and code under test may still commit/rollback savepoints."""
    conn = engine.connect()
    outer = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        conn.close()


@pytest.fixture
def ref(db: Session) -> Session:
    """Database with exchanges and the sector taxonomy seeded."""
    seed_reference(db)
    return db


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db
    with TestClient(app) as c:
        yield c
