import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient

# Point the app at the dedicated test database *before* any app module reads settings.
_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
_test_url = os.environ.get("TEST_DATABASE_URL") or dotenv_values(_ROOT_ENV).get("TEST_DATABASE_URL")
if not _test_url:
    pytest.exit("TEST_DATABASE_URL is not set (env var or repo-root .env).", returncode=2)
os.environ["DATABASE_URL"] = _test_url
os.environ["APP_ENV"] = "test"

from app.config import get_settings  # noqa: E402
from app.db import get_engine  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    get_settings.cache_clear()
    get_engine.cache_clear()
    with TestClient(create_app()) as c:
        yield c
