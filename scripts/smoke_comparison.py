"""Verify model comparison and exact original quotes against official samples."""

import argparse
import json
from urllib.request import Request, urlopen


def smoke(base_url):
    def read(path, data=None):
        request = Request(
            base_url + "/api/v1" + path,
            data=json.dumps(data).encode() if data is not None else None,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=200) as response:
            return json.load(response)

    items = read("/patents?number=202640162&number_type=publication")["items"]
    fulltext = next(row for row in items if row["content_scope"] == "fulltext")
    metadata = next(
        row for row in items if row["content_scope"] == "metadata_and_abstract"
    )
    path = f"/patents/{fulltext['document_id']}"
    feature = dict(
        feature_id="f1",
        description_zh="動態導通電阻量測電路",
        keywords_zh=["動態導通電阻"],
        keywords_en=[],
        must_have=True,
        confidence="high",
        ipc_candidates=[],
    )
    response = read(path + "/compare", {"features": [feature]})
    assert response["document_id"] == fulltext["document_id"]
    [item] = response["items"]
    assert item["verdict"] in {"supported", "partially_supported"}
    evidence = item["evidence"]
    assert evidence["kind"] == "claim"
    claim = next(
        row
        for row in read(path + "/claims")["claims"]
        if row["claim_number"] == evidence["ordinal"]
    )
    assert (
        claim["text"][evidence["char_start"] : evidence["char_end"]]
        == evidence["quote"]
    )
    assert claim["source"]["xpath"] == evidence["xpath"]
    assert claim["source"]["artifact_sha256"] == evidence["artifact_sha256"]

    empty = read(f"/patents/{metadata['document_id']}/compare", {"features": [feature]})
    assert empty["items"][0]["verdict"] == "uncertain"
    assert empty["items"][0]["evidence"] is None

    absent = read(
        path + "/compare",
        {
            "features": [
                {
                    **feature,
                    "description_zh": "不存在的測試字串甲乙丙丁",
                    "keywords_zh": [],
                }
            ]
        },
    )
    assert absent["items"][0]["verdict"] == "not_found_in_checked_content"
    assert absent["items"][0]["evidence"] is None
    print(
        f"Comparison smoke passed: {item['verdict']}, exact quote, version isolation and missing evidence"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:18008")
    smoke(parser.parse_args().api)
