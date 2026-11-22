from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.db import get_engine
from app.main import create_app


def test_health_ok_with_real_database(client: TestClient) -> None:
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["environment"] == "test"
    assert body["checks"]["database"]["status"] == "ok"
    assert body["checks"]["database"]["latency_ms"] >= 0


def test_health_503_when_database_unreachable(client: TestClient) -> None:
    # Port 1 on localhost: a real connection attempt that is refused, no mocking.
    dead = create_engine(
        "postgresql+psycopg://nobody:nothing@127.0.0.1:1/none", connect_args={"connect_timeout": 1}
    )
    client.app.dependency_overrides[get_engine] = lambda: dead  # type: ignore[attr-defined]
    res = client.get("/api/v1/health")
    assert res.status_code == 503
    body = res.json()
    assert body["status"] == "error"
    assert body["checks"]["database"] == {"status": "error", "latency_ms": None}
    assert "nobody" not in res.text  # no connection details leaked


def test_health_rejects_wrong_method(client: TestClient) -> None:
    assert client.post("/api/v1/health").status_code == 405


def test_unknown_route_is_404(client: TestClient) -> None:
    assert client.get("/api/v1/does-not-exist").status_code == 404


def test_unhandled_error_returns_generic_500() -> None:
    app = create_app()

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("secret internal detail")

    res = TestClient(app, raise_server_exceptions=False).get("/boom")
    assert res.status_code == 500
    assert res.json() == {"detail": "Internal server error"}
    assert "secret" not in res.text
