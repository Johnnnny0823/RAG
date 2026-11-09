"""Verify owner isolation and immutable saved results against real TIPO data."""

import argparse
import json
import secrets
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


def smoke(base_url):
    def call(path, *, payload=None, token=None, status=200):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = Request(
            base_url + "/api/v1" + path,
            headers=headers,
            data=json.dumps(payload).encode() if payload is not None else None,
        )
        try:
            with urlopen(request, timeout=300) as response:
                assert response.status == status
                return json.load(response)
        except HTTPError as error:
            assert error.code == status, (path, error.code)
            return json.load(error)

    def new_account():
        payload = {
            "email": f"demo-{uuid4().hex}@example.invalid",
            "password": secrets.token_urlsafe(24),
        }
        account = call("/auth/register", payload=payload, status=201)
        token = call("/auth/login", payload=payload)["access_token"]
        assert call("/me", token=token) == account
        return token

    first, second = new_account(), new_account()
    feature = dict(
        feature_id="f1",
        description_zh="動態導通電阻量測電路",
        keywords_zh=["動態導通電阻"],
        keywords_en=[],
        must_have=True,
        confidence="high",
        ipc_candidates=[],
    )
    request = {
        "query": "動態導通電阻量測",
        "features": [feature],
        "ipc": "G01R27/02",
        "limit": 1,
        "rerank": True,
    }
    call("/search-runs", payload=request, status=401)
    run = call("/search-runs", payload=request, token=first, status=201)
    path = "/search-runs/" + run["id"]
    assert call(path, token=second, status=404)["error"]["code"] == "RUN_NOT_FOUND"
    assert not call("/search-runs", token=second)
    assert run in call("/search-runs", token=first)
    details = call(path, token=first)
    assert details["request"]["query"] == request["query"]
    assert details["settings"]["reranker"]["model_digest"]
    assert len(details["items"]) > request["limit"]
    hit = next(
        item
        for item in details["items"]
        if item["publication_no"] == "202640162" and item["content_scope"] == "fulltext"
    )
    compare_path = path + "/comparisons/" + hit["document_id"]
    call(compare_path, payload={}, token=second, status=404)
    comparison = call(compare_path, payload={}, token=first)
    assert comparison["document_id"] == hit["document_id"]
    evidence = comparison["items"][0]["evidence"]
    assert evidence and evidence["quote"]
    assert call(compare_path, payload={}, token=first) == comparison
    after = call(path, token=first)
    assert after["items"] == details["items"]
    assert after["comparisons"] == [comparison]
    print(
        "Saved-search smoke passed: login, ownership, complete rankings and immutable evidence"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:18010")
    smoke(parser.parse_args().api)
