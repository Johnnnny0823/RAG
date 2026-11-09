import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.retrieval.embeddings import (
    DIMENSIONS,
    EmbeddingError,
    LocalEmbeddingModel,
)
from services.retrieval.index_semantic import windows


def test_model_refuses_an_external_url(monkeypatch):
    monkeypatch.setenv("EMBEDDING_URL", "http://example.com:11434")
    monkeypatch.setenv("EMBEDDING_MODEL", "example:latest")
    monkeypatch.setenv("EMBEDDING_DIGEST", "a" * 64)
    with pytest.raises(EmbeddingError, match="local Ollama"):
        LocalEmbeddingModel.from_env()


def test_embed_checks_model_digest_and_rejects_invalid_vectors(monkeypatch):
    model = LocalEmbeddingModel("http://127.0.0.1:11434", "model:tag", "a" * 64)
    calls = []

    def request(self, path, payload=None):
        calls.append(path)
        if path == "/api/tags":
            return {"models": [{"name": model.name, "digest": model.digest}]}
        assert payload["input"] == ["public corpus text"]
        return {"model": model.name, "embeddings": [[0.0] * DIMENSIONS]}

    monkeypatch.setattr(LocalEmbeddingModel, "request_json", request)
    with pytest.raises(EmbeddingError, match="Invalid embedding"):
        model.embed(["public corpus text"])
    assert calls == ["/api/tags", "/api/embed", "/api/tags"]
    monkeypatch.setattr(
        LocalEmbeddingModel, "request_json", lambda *args: {"models": []}
    )
    with pytest.raises(EmbeddingError, match="digest"):
        model.embed(["public corpus text"])


def test_semantic_windows_retain_exact_character_offsets():
    body = "甲" * 999 + "乙丙"
    parts = list(windows(body))
    assert [(start, end) for start, end, _ in parts] == [(0, 1000), (900, 1001)]
    assert all(text == body[start:end] for start, end, text in parts)
    assert list(windows(" ")) == []


def test_semantic_endpoint_reports_disabled_provider(monkeypatch):
    monkeypatch.delenv("EMBEDDING_URL", raising=False)
    response = TestClient(app).post(
        "/api/v1/patents/search/semantic", json={"query": "電阻"}
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "EMBEDDING_UNAVAILABLE"
