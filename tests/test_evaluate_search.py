from pytest import approx

from scripts.evaluate_search import score


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
