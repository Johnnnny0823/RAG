"""Exercise hybrid retrieval against the official M1 sample corpus."""

import argparse
import json
from math import isclose
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def smoke(base_url: str) -> None:
    def search(path, query, ipc, **paging):
        request = Request(
            f"{base_url}/api/v1/patents/search{path}",
            data=json.dumps(dict(query=query, ipc=ipc, **paging)).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=100) as response:
            return json.load(response)

    query, ipc = "動態導通電阻", "G01R27/02"
    result = search("/hybrid", query, ipc, limit=10)
    items = result["items"]
    keys = {
        (item["publication_no"], item["document_stage"], item["kind_code"])
        for item in items
    }
    assert len(keys) == len(items)
    assert ("202640162", "publication", None) in keys
    assert ("I941082", "grant", None) in keys
    assert any(item["lexical_rank"] and item["semantic_rank"] for item in items)

    for path, branch in [("", "lexical"), ("/semantic", "semantic")]:
        rows = search(path, query, ipc, limit=result["candidate_limit"])["items"]
        ranks = {row["document_id"]: (i, row["score"]) for i, row in enumerate(rows, 1)}
        for item in items:
            expected_rank, expected_score = ranks.get(item["document_id"], (None, None))
            assert item[f"{branch}_rank"] == expected_rank
            if expected_score is None:
                assert item[f"{branch}_score"] is None
            else:
                assert isclose(item[f"{branch}_score"], expected_score, abs_tol=1e-5)

    for item in items:
        assert isclose(
            item["rrf_score"],
            sum(
                1 / (result["rrf_k"] + rank)
                for rank in (item["lexical_rank"], item["semantic_rank"])
                if rank is not None
            ),
        )

    first = search("/hybrid", query, ipc, limit=1)
    second = search("/hybrid", query, ipc, limit=1, offset=1)
    assert (
        first["has_more"]
        and first["items"][0]["document_id"] != second["items"][0]["document_id"]
    )
    assert not search("/hybrid", query, "H01B9999/999999")["items"]
    for path in ("", "/semantic", "/hybrid"):
        filtered = search(
            path,
            query,
            ipc,
            document_stage="publication",
            applicant="yang ming chiao tung",
        )["items"]
        assert any(item["publication_no"] == "202640162" for item in filtered)
        assert all(item["document_stage"] == "publication" for item in filtered)
        assert not search(path, query, ipc, applicant="%")["items"]
        dated = search(path, query, ipc, published_from="2000-01-01")["items"]
        assert all(item["publication_date"] >= "2000-01-01" for item in dated)
        try:
            search(
                path, query, ipc, published_from="2026-10-02", published_to="2026-10-01"
            )
        except HTTPError as error:
            assert (
                error.code == 422
                and json.load(error)["error"]["code"] == "INVALID_REQUEST"
            )
        else:
            raise AssertionError("Reversed date range must be rejected")
    print(
        "Hybrid smoke passed: real candidates, branch ranks, RRF, version deduplication, metadata filters and pagination"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:18006")
    smoke(parser.parse_args().api)
