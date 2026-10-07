from collections.abc import Iterator
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.dependencies import get_db
from app.main import app


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["database"] == "ok"


def test_health_reports_database_unavailable(client: TestClient) -> None:
    class BrokenSession:
        def execute(self, *_: Any, **__: Any) -> None:
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    def broken_db() -> Iterator[BrokenSession]:
        yield BrokenSession()

    app.dependency_overrides[get_db] = broken_db
    response = client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "DATABASE_UNAVAILABLE"


def test_unknown_route_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "message": "Không tìm thấy đường dẫn",
        "error": {"code": "NOT_FOUND"},
    }
