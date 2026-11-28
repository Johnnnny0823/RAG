from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore, Event

from fastapi.testclient import TestClient

from services.api import model_limits, patents, queries
from services.api.main import app
from services.retrieval.embeddings import EmbeddingError, LocalEmbeddingModel
from services.retrieval.ollama import LocalOllamaModel


def test_embedding_blocks_concurrent_analysis_and_releases_after_error(monkeypatch):
    monkeypatch.setattr(model_limits, "_slots", BoundedSemaphore(1))
    monkeypatch.setattr(
        LocalEmbeddingModel, "from_env", lambda: LocalEmbeddingModel("", "", "")
    )
    monkeypatch.setattr(patents, "indexed_model_id", lambda _: 1)
    monkeypatch.setattr(
        LocalOllamaModel, "from_env", lambda _: LocalOllamaModel("", "", "")
    )
    monkeypatch.setattr(queries, "analyze_features", lambda *_: [])
    entered = Event()
    release = Event()

    def fail_embedding(*_):
        entered.set()
        assert release.wait(10)
        raise EmbeddingError("DEMO model failure")

    monkeypatch.setattr(LocalEmbeddingModel, "embed_query", fail_embedding)
    with TestClient(app) as client, ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(
            client.post, "/api/v1/patents/search/semantic", json={"query": "DEMO"}
        )
        try:
            assert entered.wait(10)
            busy = client.post("/api/v1/queries/analyze", json={"query": "DEMO"})
            assert busy.status_code == 429
            assert busy.headers["Retry-After"] == "5"
            assert busy.headers["Cache-Control"] == "no-store"
            assert busy.json()["error"]["code"] == "MODEL_BUSY"
            assert client.get("/api/v1/health").status_code == 200
        finally:
            release.set()
        failed = pending.result(timeout=10)
        assert failed.status_code == 503
        assert failed.json()["error"]["code"] == "EMBEDDING_UNAVAILABLE"
        assert (
            client.post("/api/v1/queries/analyze", json={"query": "DEMO"}).status_code
            == 200
        )
