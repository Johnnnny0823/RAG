from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from services.api.audit import AuditLogEntry
from services.api.identity import Account, require_account
from services.api.main import app


def test_audit_logs_require_authentication():
    client = TestClient(app)
    response = client.get("/api/v1/audit-logs")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_audit_logs_return_owner_entries(monkeypatch):
    owner = Account(id=uuid4(), email="audit-owner@example.invalid")
    sample = [
        AuditLogEntry(
            id=1,
            action="report.export",
            resource_type="search_run",
            resource_id=str(uuid4()),
            outcome="success",
            created_at=datetime(2026, 11, 27, 1, 0, tzinfo=timezone.utc),
        )
    ]
    app.dependency_overrides[require_account] = lambda: owner
    monkeypatch.setattr(
        "services.api.audit.fetch_owner_audit_logs",
        lambda user_id, limit, offset: (sample if user_id == owner.id else [], False),
    )
    try:
        client = TestClient(app)
        response = client.get("/api/v1/audit-logs")
        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        body = response.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["action"] == "report.export"
        assert body["has_more"] is False
    finally:
        app.dependency_overrides.pop(require_account, None)
