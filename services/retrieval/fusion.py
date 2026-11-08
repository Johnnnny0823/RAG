"""Fuse document-version rankings without borrowing scores across versions."""

from collections.abc import Mapping, Sequence
from typing import Any

RRF_K = 60
CANDIDATE_LIMIT = 100


def fuse_rankings(
    lexical: Sequence[Mapping[str, Any]],
    semantic: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    candidates = {}
    for branch, rows in (("lexical", lexical), ("semantic", semantic)):
        for rank, row in enumerate(rows, 1):
            document_id = row["document_id"]
            hit = candidates.setdefault(
                document_id,
                {
                    **row,
                    "lexical_rank": None,
                    "lexical_score": None,
                    "semantic_rank": None,
                    "semantic_score": None,
                },
            )
            if hit[f"{branch}_rank"] is None:
                hit[f"{branch}_rank"] = rank
                hit[f"{branch}_score"] = row["score"]

    for hit in candidates.values():
        hit.pop("score")
        hit["rrf_score"] = sum(
            1 / (RRF_K + rank)
            for rank in (hit["lexical_rank"], hit["semantic_rank"])
            if rank is not None
        )

    scope_order = {"fulltext": 0, "claims_only": 1, "metadata_and_abstract": 2}
    ordered = sorted(
        candidates.values(),
        key=lambda hit: (
            -hit["rrf_score"],
            scope_order[hit["content_scope"]],
            hit["document_id"],
        ),
    )
    distinct = {}
    for hit in ordered:
        key = (hit["document_stage"], hit["publication_no"], hit["kind_code"])
        distinct.setdefault(key, hit)
    return list(distinct.values())
