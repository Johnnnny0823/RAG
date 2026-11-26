from pytest import approx, raises

from scripts import evaluate_search
from scripts.evaluate_search import (
    build_review_pool,
    check_reviewed_version,
    evaluate,
    score,
)


def test_duplicate_versions_consume_rank_and_only_first_earns_credit():
    items = [
        {"document_stage": "publication", "publication_no": "A"},
        {"document_stage": "publication", "publication_no": "A"},
        {"document_stage": "grant", "publication_no": "B"},
    ]
    result = score(items, {("publication", "A"): 2, ("grant", "B"): 1})
    assert result["precision_at_10_lower_bound"] == 0.2
    assert result["recall_at_10_relative_to_pool"] == 1
    assert result["ndcg_at_10_relative_to_pool"] == approx(0.964, abs=0.001)


def test_unjudged_and_missing_documents_do_not_earn_credit():
    result = score(
        [{"document_stage": "grant", "publication_no": "A"}],
        {("publication", "A"): 2},
    )
    assert result["unjudged_returned"] == 1
    assert result["reciprocal_rank"] == 0
    assert result["recall_at_10_relative_to_pool"] == 0


def test_reviewed_case_with_no_relevant_documents_remains_in_evaluation(monkeypatch):
    monkeypatch.setattr(evaluate_search, "version_details", lambda *_: iter(()))
    monkeypatch.setattr(evaluate_search, "check_reviewed_version", lambda *_: None)
    corpus = {"documents_total": 1, "semantic_indexed_documents": 1}

    def request(_api, path, *_args):
        return corpus if path == "/corpus/status" else {"items": []}

    monkeypatch.setattr(evaluate_search, "request", request)
    dataset = {
        "label_status": "human_reviewed",
        "reviewer": "DEMO reviewer",
        "cases": [
            {
                "id": "all-unrelated",
                "query": "DEMO query",
                "judgments": [
                    {
                        "stage": "grant",
                        "number": "DEMO",
                        "grade": 0,
                        "basis": "DEMO reason",
                    }
                ],
            }
        ],
    }
    result = evaluate("", dataset, 1)
    assert result["corpus_status"] == corpus
    assert len(result["dataset_sha256"]) == 64
    reordered = dict(reversed(list(dataset.items())))
    assert evaluate("", reordered, 1)["dataset_sha256"] == result["dataset_sha256"]
    changed = {**dataset, "reviewer": "DEMO second reviewer"}
    assert evaluate("", changed, 1)["dataset_sha256"] != result["dataset_sha256"]
    for summary in result["summary"].values():
        assert summary["precision_at_10_lower_bound"] == 0
        assert summary["recall_at_10_relative_to_pool"] is None
        assert summary["ndcg_at_10_relative_to_pool"] is None
        assert summary["runs_with_relevant_judgments"] == 0


def test_evaluation_rejects_corpus_drift_between_searches(monkeypatch):
    corpus_status = iter(
        [{"semantic_indexed_documents": 1}, {"semantic_indexed_documents": 2}]
    )

    def request(_api, path, *_args):
        return next(corpus_status) if path == "/corpus/status" else {"items": []}

    monkeypatch.setattr(evaluate_search, "request", request)
    monkeypatch.setattr(evaluate_search, "version_details", lambda *_: iter([{}]))
    dataset = {
        "label_status": "seed",
        "cases": [
            {
                "id": "DEMO",
                "query": "DEMO query",
                "judgments": [{"stage": "grant", "number": "DEMO", "grade": 1}],
            }
        ],
    }
    with raises(ValueError, match="Corpus status changed"):
        evaluate("", dataset, 1)


def test_human_review_requires_reviewer_and_written_basis():
    dataset = {
        "label_status": "human_reviewed",
        "cases": [{"id": "example", "judgments": [{"grade": 2, "basis": ""}]}],
    }
    with raises(ValueError, match="require a reviewer"):
        evaluate("", dataset, 1)
    with raises(ValueError, match="require a basis"):
        evaluate("", {**dataset, "reviewer": "example-reviewer"}, 1)


def test_review_pool_pins_richest_available_version(monkeypatch):
    metadata = {"document_id": "metadata", "content_scope": "metadata_and_abstract"}
    fulltext = {
        "document_id": "fulltext",
        "content_scope": "fulltext",
        "document_sha256": "a" * 64,
        "parser_version": "example-v1",
        "title_zh": "Fixture",
        "sources": [],
    }

    def fixture_request(api, path):
        if path.startswith("/patents?"):
            return {"items": [metadata, fulltext], "has_more": False}
        assert path == "/patents/fulltext"
        return fulltext

    monkeypatch.setattr(evaluate_search, "request", fixture_request)
    dataset = {"cases": [{"id": "example", "query": "fixture", "judgments": []}]}
    evaluation = {
        "runs": {
            "lexical": [
                {
                    "case": "example",
                    "results": [
                        {
                            **metadata,
                            "document_stage": "publication",
                            "publication_no": "A",
                        }
                    ],
                }
            ]
        },
    }
    pool = build_review_pool("", dataset, evaluation)
    row = pool["cases"][0]["judgments"][0]
    assert row["document_sha256"] == "a" * 64
    assert row["parser_version"] == "example-v1"
    assert row["grade"] is None and not row["basis"]
    assert "lexical" not in row
    check_reviewed_version(
        "", {**row, "document_id": "different-db-id"}, iter([fulltext])
    )
    with raises(ValueError, match="Reviewed version missing"):
        check_reviewed_version(
            "", {**row, "document_sha256": "b" * 64}, iter([fulltext])
        )


def test_pending_pool_does_not_produce_scores():
    with raises(ValueError, match="pending human review"):
        evaluate(
            "",
            {"label_status": "pending_human_review", "cases": [{"id": "example"}]},
            1,
        )
