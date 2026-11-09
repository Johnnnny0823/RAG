import json

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.retrieval.ollama import LocalModelError, LocalOllamaModel
from services.retrieval.query_features import (
    TechnicalFeature,
    analyze_features,
    expand_query,
)

FEATURE = {
    "description_zh": "量測導通電阻",
    "keywords_zh": ["導通電阻"],
    "keywords_en": ["on resistance"],
    "must_have": True,
    "confidence": "medium",
    "ipc_candidates": ["G01R"],
}


def test_analysis_validates_schema_and_assigns_stable_feature_ids(monkeypatch):
    model = LocalOllamaModel("http://127.0.0.1:11434", "demo:tag", "a" * 64)
    monkeypatch.setattr(LocalOllamaModel, "verify_digest", lambda self: None)

    def request(self, path, payload, *, timeout):
        assert path == "/api/chat" and not payload["stream"]
        assert timeout == 180
        assert payload["format"] == "json" and "tools" not in payload
        assert "keywords_en" in payload["messages"][0]["content"]
        return {
            "model": model.name,
            "done_reason": "stop",
            "message": {
                "content": json.dumps(
                    {"features": [dict(FEATURE, technology_category="ignored")]}
                )
            },
        }

    monkeypatch.setattr(LocalOllamaModel, "request_json", request)
    [feature] = analyze_features(model, "量測導通電阻")
    assert feature.feature_id == "f1"
    assert feature.keywords_en == ["on resistance"]
    assert "technology_category" not in feature.model_dump()
    monkeypatch.setattr(LocalOllamaModel, "request_json", lambda *args, **kwargs: {})
    with pytest.raises(LocalModelError):
        analyze_features(model, "量測導通電阻")


def test_expansion_uses_only_reviewed_fields_and_preserves_original():
    feature = TechnicalFeature(feature_id="f1", **FEATURE)
    lexical, semantic = expand_query("量測", [feature])
    assert "(won & wresistance)" in lexical
    assert semantic.startswith("量測\n") and "導通電阻" in semantic
    edited = feature.model_copy(update={"keywords_en": ["thermal sheet"]})
    lexical, semantic = expand_query("量測", [edited])
    assert "(wthermal & wsheet)" in lexical and "wresistance" not in lexical
    assert "thermal sheet" in semantic and "on resistance" not in semantic
    assert "G01R" not in semantic


def test_duplicate_feature_ids_fail_before_model_call():
    payload = {"query": "量測", "features": [dict(FEATURE, feature_id="f1")] * 2}
    response = TestClient(app).post("/api/v1/patents/search/hybrid", json=payload)
    assert response.status_code == 422


def test_analyzer_disabled_reports_unavailable(monkeypatch):
    monkeypatch.delenv("ANALYSIS_URL", raising=False)
    response = TestClient(app).post("/api/v1/queries/analyze", json={"query": "量測"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ANALYSIS_UNAVAILABLE"
