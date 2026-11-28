import json

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.patents import HybridSearchRequest, RankedSearchRequest
from services.api.queries import AnalyzeRequest
from services.retrieval.ollama import LocalModelError, LocalOllamaModel
from services.retrieval.query_features import (
    TechnicalFeature,
    MAX_INVENTION_LENGTH,
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


@pytest.mark.parametrize("query", ["量測導通電阻", "量測導通電阻。" * 40])
def test_analysis_validates_schema_and_assigns_stable_feature_ids(monkeypatch, query):
    model = LocalOllamaModel("http://127.0.0.1:11434", "demo:tag", "a" * 64)
    monkeypatch.setattr(LocalOllamaModel, "verify_digest", lambda self: None)

    def request(self, path, payload, *, timeout):
        assert path == "/api/chat" and not payload["stream"]
        assert timeout == 180
        if len(query) > 160:
            assert payload["format"]["properties"]["features"]["maxItems"] == 5
            assert payload["options"]["num_ctx"] == 8192
        else:
            assert payload["format"] == "json"
        assert "tools" not in payload
        assert payload["messages"][1]["content"] == query
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
    [feature] = analyze_features(model, query)
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


def test_long_query_retains_original_and_all_reviewed_feature_descriptions():
    query = ("量測導通電阻。" * MAX_INVENTION_LENGTH)[:MAX_INVENTION_LENGTH]
    features = [
        TechnicalFeature(
            **{
                **FEATURE,
                "feature_id": f"f{i}",
                "description_zh": f"技術特徵{i}" * 20,
                "keywords_en": ["thermal resistance"],
            }
        )
        for i in range(1, 6)
    ]
    request = HybridSearchRequest(query=query, features=features)
    assert request.model_dump()["query"] == query
    assert AnalyzeRequest(query=query).query == query
    lexical, semantic = expand_query(request.query, request.features)
    assert len(lexical.split(" | ")) == 4
    assert "(wthermal & wresistance)" in lexical
    assert semantic.splitlines() == [
        query,
        *(feature.description_zh for feature in features),
    ]
    with pytest.raises(ValueError):
        RankedSearchRequest(query=query)


@pytest.mark.parametrize("path", ["/queries/analyze", "/patents/search/hybrid"])
def test_overlong_invention_rejected_before_model_access(path):
    response = TestClient(app).post(
        "/api/v1" + path, json={"query": "甲" * (MAX_INVENTION_LENGTH + 1)}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_duplicate_feature_ids_fail_before_model_call():
    payload = {"query": "量測", "features": [dict(FEATURE, feature_id="f1")] * 2}
    response = TestClient(app).post("/api/v1/patents/search/hybrid", json=payload)
    assert response.status_code == 422


def test_analyzer_disabled_reports_unavailable(monkeypatch):
    monkeypatch.delenv("ANALYSIS_URL", raising=False)
    response = TestClient(app).post("/api/v1/queries/analyze", json={"query": "量測"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ANALYSIS_UNAVAILABLE"
