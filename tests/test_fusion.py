from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.retrieval.fusion import RRF_K, fuse_rankings


def hit(
    index, number="DEMO-publication", stage="publication", scope="fulltext", score=1.0
):
    return {
        "document_id": UUID(int=index),
        "publication_no": number,
        "document_stage": stage,
        "kind_code": None,
        "content_scope": scope,
        "score": score,
    }


def test_fusion_deduplicates_versions_without_combining_different_version_ranks():
    metadata = hit(1, scope="metadata_and_abstract")
    fulltext = hit(2, score=0.7)
    grant = hit(3, number="DEMO-grant", stage="grant")
    lexical = [metadata, grant, grant]
    semantic = [fulltext, grant]
    result = fuse_rankings(lexical, semantic)

    assert [row["document_id"] for row in result] == [
        grant["document_id"],
        fulltext["document_id"],
    ]
    assert result[0]["rrf_score"] == pytest.approx(2 / (RRF_K + 2))
    assert result[1]["rrf_score"] == pytest.approx(1 / (RRF_K + 1))
    assert result[1]["semantic_rank"] == 1
    assert result[1]["semantic_score"] == 0.7
    assert result[1]["lexical_rank"] is None
    assert "rrf_score" not in fulltext


def test_fusion_keeps_lexical_only_and_semantic_only_results():
    lexical = hit(1, "DEMO-lexical")
    semantic = hit(2, "DEMO-semantic")
    result = fuse_rankings([lexical], [semantic])
    assert [row["document_id"] for row in result] == [
        lexical["document_id"],
        semantic["document_id"],
    ]
    assert result[0]["semantic_rank"] is None
    assert result[1]["lexical_rank"] is None
    assert not fuse_rankings([], [])


def test_hybrid_reports_unconfigured_embedding(monkeypatch):
    monkeypatch.delenv("EMBEDDING_URL", raising=False)
    response = TestClient(app).post(
        "/api/v1/patents/search/hybrid", json={"query": "電阻"}
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "EMBEDDING_UNAVAILABLE"
