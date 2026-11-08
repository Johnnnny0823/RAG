from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from services.api import main

client = TestClient(main.app)


def unavailable():
    raise OperationalError(None, None, Exception("private connection details"))


def test_liveness_is_independent_of_database(monkeypatch):
    monkeypatch.setattr(main, "check_database", unavailable)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_success(monkeypatch):
    monkeypatch.setattr(main, "check_database", lambda: None)
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert response.headers["cache-control"] == "no-store"


def test_ready_returns_safe_service_unavailable(monkeypatch):
    monkeypatch.setattr(main, "check_database", unavailable)
    response = client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    error = response.json()["error"]
    assert error["code"] == "DATABASE_UNAVAILABLE"
    assert UUID(error["request_id"])
    assert "private connection details" not in response.text


def test_openapi_documents_readiness_failure():
    responses = client.get("/openapi.json").json()["paths"]["/api/v1/ready"]["get"][
        "responses"
    ]
    assert {"200", "503"} <= responses.keys()
