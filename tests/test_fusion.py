from uuid import UUID
from contextlib import nullcontext
from datetime import UTC, datetime, date
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api import patents
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


def test_hybrid_api_sorts_dates_before_pagination_and_keeps_fusion_ranks(monkeypatch):
    model = Mock(name="embedding")
    model.name = "DEMO-model"
    model.digest = "DEMO-digest"
    model.embed_query.return_value = [1.0]
    monkeypatch.setattr(patents.LocalEmbeddingModel, "from_env", lambda: model)
    monkeypatch.setattr(patents, "indexed_model_id", lambda _: 1)
    conn = Mock()
    conn.execution_options.return_value = nullcontext(conn)
    conn.exec_driver_sql.return_value.mappings.return_value.one.return_value = {
        "observed_at": datetime.now(UTC),
        "lexical_versions": 4,
        "semantic_versions": 4,
        "latest_document_date": date(2026, 1, 1),
    }
    monkeypatch.setattr(patents.engine, "connect", lambda: conn)
    dates = [None, date(2025, 1, 1), date(2026, 1, 1), date(2026, 1, 1)]
    rows = [
        {
            **hit(i, number=f"DEMO-{i}"),
            "publication_date": published,
            "application_no": f"DEMO-{i}",
            "filing_date": None,
            "title_zh": None,
            "title_en": None,
        }
        for i, published in enumerate(dates, 1)
    ]
    monkeypatch.setattr(patents, "lexical_rows", lambda *_: rows)
    monkeypatch.setattr(patents, "semantic_rows", lambda *_: rows)
    conn.exec_driver_sql.return_value.mappings.return_value.__iter__ = lambda _: iter(
        [
            {
                "id": row["document_id"],
                "abstract_excerpt": row["publication_no"],
                "applicants": [{"zh": "DEMO applicant"}],
                "ipc_codes": ["G01R27/02"],
            }
            for row in rows
        ]
    )
    monkeypatch.setattr(
        patents,
        "document_sources_by_id",
        lambda *_: {
            rows[3]["document_id"]: [
                Mock(dataset_url="https://data.gov.tw/dataset/15987")
            ]
        },
    )
    client = TestClient(app)
    response = client.post(
        "/api/v1/patents/search/hybrid",
        json={
            "query": "電阻",
            "sort_by": "date_desc",
            "limit": 2,
            "offset": 1,
        },
    )
    assert response.status_code == 200
    assert [
        (row["publication_no"], row["fusion_rank"]) for row in response.json()["items"]
    ] == [
        ("DEMO-4", 4),
        ("DEMO-2", 2),
    ]
    first, second = response.json()["items"]
    assert first["abstract_excerpt"] == "DEMO-4"
    assert first["applicants"] == [{"zh": "DEMO applicant", "en": None}]
    assert first["ipc_codes"] == ["G01R27/02"]
    assert first["official_source_url"] == "https://data.gov.tw/dataset/15987"
    assert second["official_source_url"] is None
