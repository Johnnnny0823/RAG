import json
import logging

from fastapi.testclient import TestClient

from services.api.main import app


def test_activity_records_route_template_and_outcome_without_input(caplog):
    client = TestClient(app)
    caplog.set_level(logging.INFO, logger="uvicorn.error")
    private_id = "4cd9ce9a-a1a3-408d-9d9b-a56bf4b551d5"
    response = client.post(
        f"/api/v1/patents/{private_id}/compare?text=private-query",
        headers={"Authorization": "Bearer example-private-token"},
        json={"features": "private-invention"},
    )
    assert response.status_code == 422
    assert client.get("/api/v1/me/export").status_code == 401
    assert client.get("/api/v1/health").status_code == 200

    events = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "uvicorn.error"
    ]
    assert [(event["method"], event["route"], event["status"]) for event in events] == [
        ("POST", "/api/v1/patents/{document_id}/compare", 422),
        ("GET", "/api/v1/me/export", 401),
    ]
    for event in events:
        assert set(event) == {"event", "method", "route", "status", "duration_ms"}
        assert event["event"] == "api_activity"
        assert event["duration_ms"] >= 0
