from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from services.api import patents
from services.api.main import app

client = TestClient(app)


@pytest.mark.parametrize(
    ("path", "code"),
    [
        (
            "/api/v1/patents?number=I941082&number_type=publication",
            "INVALID_PATENT_NUMBER",
        ),
        ("/api/v1/patents?number=202640162&number_type=unknown", "INVALID_REQUEST"),
        (
            "/api/v1/patents?number=202640162&number_type=publication&limit=0",
            "INVALID_REQUEST",
        ),
        ("/api/v1/patents/not-a-uuid/claims", "INVALID_REQUEST"),
    ],
)
def test_patent_input_errors_have_a_machine_readable_code(path, code):
    response = client.get(path)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == code
    assert UUID(error["request_id"])


def test_patent_database_failure_returns_503_without_connection_details(monkeypatch):
    def unavailable():
        raise OperationalError(None, None, RuntimeError("private connection details"))

    monkeypatch.setattr(patents.engine, "connect", unavailable)
    response = client.get("/api/v1/patents?number=202640162&number_type=publication")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATA_SOURCE_UNAVAILABLE"
    assert "private connection details" not in response.text


def test_query_number_normalization_keeps_leading_zeroes():
    assert (
        patents.normalize_number(" ０９１１３２００１ ", "application") == "091132001"
    )
    assert patents.normalize_number(" ｉ９４１０８２ ", "grant") == "I941082"


def test_source_url_omits_unverified_links_and_tokens():
    assert patents.source_url("index.xml") is None
    assert patents.source_url("https://cloud.tipo.gov.tw/a?tk=private") is None
    assert patents.source_url("https://not-tipo.example/a") is None
    assert (
        patents.source_url("https://data.gov.tw/dataset/15996")
        == "https://data.gov.tw/dataset/15996"
    )
