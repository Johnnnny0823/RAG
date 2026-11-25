from scripts.explain_search import summarize_plan


def test_plan_artifact_keeps_index_and_buffer_evidence_without_bound_values():
    raw = {
        "Node Type": "Sort",
        "Sort Key": ["embedding <=> '[1,2]'::vector"],
        "Actual Rows": 4,
        "Plans": [
            {
                "Node Type": "Bitmap Index Scan",
                "Index Name": "ix_example",
                "Index Cond": "terms @@ 'private input'",
                "Shared Hit Blocks": 2,
            }
        ],
    }
    assert summarize_plan(raw) == {
        "Node Type": "Sort",
        "Actual Rows": 4,
        "Plans": [
            {
                "Node Type": "Bitmap Index Scan",
                "Index Name": "ix_example",
                "Shared Hit Blocks": 2,
            }
        ],
    }
