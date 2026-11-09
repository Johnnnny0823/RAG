"""Verify local technical feature extraction and reviewed query expansion."""

import argparse
import json
from urllib.request import Request, urlopen


def smoke(base_url: str) -> None:
    def post(path, payload):
        request = Request(
            base_url + "/api/v1" + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=200) as response:
            return json.load(response)

    query = "以多孔凝膠製成低熱傳導片材，並從模具中央灌入前驅材料，使厚度保持均勻。"
    draft = post("/queries/analyze", {"query": query})
    assert draft["analysis_version"] == "technical-features-v1"
    assert len(draft["model_digest"]) == 64
    features = draft["features"]
    assert 1 <= len(features) <= 5
    assert any(item["keywords_zh"] and item["keywords_en"] for item in features)

    payload = {"query": query, "ipc": "B01J"}
    before = post("/patents/search/hybrid", payload)
    reviewed = {
        **features[0],
        "description_zh": "製作氣凝膠隔熱片",
        "keywords_zh": ["氣凝膠隔熱片"],
        "keywords_en": ["aerogel thermal insulation sheet"],
    }
    after = post("/patents/search/hybrid", {**payload, "features": [reviewed]})
    assert before["applied_feature_ids"] == []
    assert after["applied_feature_ids"] == [reviewed["feature_id"]]
    expected = "202637274"
    assert not any(
        item["publication_no"] == expected and item["lexical_rank"]
        for item in before["items"]
    )
    matching = [item for item in after["items"] if item["publication_no"] == expected]
    assert matching and matching[0]["lexical_rank"] and matching[0]["semantic_rank"]
    print(
        f"Query-feature smoke passed: {len(features)} model features and reviewed terms hit {expected} in both branches"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:18007")
    smoke(parser.parse_args().api)
