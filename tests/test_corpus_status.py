from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from services.api.corpus import CorpusStatus, IngestionBatchSummary
from services.api.main import app


def test_corpus_status_returns_summary(monkeypatch):
    sample = CorpusStatus(
        datasets_count=2,
        documents_total=117,
        publications_count=116,
        grants_count=1,
        lexical_indexed_documents=117,
        semantic_indexed_documents=117,
        latest_ingested_at=datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc),
        recent_batches=[
            IngestionBatchSummary(
                dataset_key="tipo-pub-xml",
                batch_key="24-19",
                parser_version="tipopatentpub-1",
                status="complete",
                counts={"documents": 100},
                finished_at=datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc),
            )
        ],
    )
    monkeypatch.setattr("services.api.corpus.fetch_corpus_status", lambda: sample)
    client = TestClient(app)

    response = client.get("/api/v1/corpus/status")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    body = response.json()
    assert body["documents_total"] == 117
    assert body["publications_count"] == 116
    assert body["grants_count"] == 1
    assert body["recent_batches"][0]["batch_key"] == "24-19"


def test_corpus_status_returns_503_when_database_unavailable(monkeypatch):
    def _fail():
        raise OperationalError("SELECT 1", {}, Exception("db down"))

    monkeypatch.setattr("services.api.corpus.fetch_corpus_status", _fail)
    client = TestClient(app)

    response = client.get("/api/v1/corpus/status")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATA_SOURCE_UNAVAILABLE"
