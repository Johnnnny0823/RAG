"""Verify known-item retrieval and semantic evidence for two official grants."""

import argparse

from evaluate_citations import feature_payload, verify_citation
from evaluate_search import request

CASES = (
    (
        "M688679",
        "claims_only",
        "利用偏離光學中心的窄縫判斷拍攝樣品何時對焦",
        "adef492f39db89c809115dd68d028cbff178a3634fbcf11f38de3ab0739c3093",
    ),
    (
        "D247328",
        "metadata_and_abstract",
        "圖示中的深淺用於呈現物品立體輪廓",
        "f8c18dc5cb114fc70bd54b38a4cd8ea97b57772adac3568603e88c36c3e83d18",
    ),
)


def smoke(api: str) -> None:
    for number, index_scope, paraphrase, artifact_sha256 in CASES:
        versions = request(api, f"/patents?number={number}&number_type=grant")["items"]
        assert [item["content_scope"] for item in versions] == ["fulltext", index_scope]
        full, index = versions
        assert full["application_no"] == index["application_no"]
        assert full["document_id"] != index["document_id"]
        for route in ("semantic", "hybrid"):
            result = request(
                api,
                f"/patents/search/{route}",
                {
                    "query": paraphrase,
                    "document_stage": "grant",
                    "content_scope": "fulltext",
                },
            )
            assert result["items"][0]["document_id"] == full["document_id"]
            assert all(item["content_scope"] == "fulltext" for item in result["items"])
            if route == "hybrid":
                assert result["corpus_coverage"]["semantic_versions"] == len(CASES)
        path = "/patents/" + full["document_id"]
        detail = request(api, path)
        claims = request(api, path + "/claims")["claims"]
        original_text = [row["original_text"] for row in detail["sections"]]
        original_text.extend(row["text"] for row in claims)
        assert all(paraphrase not in text for text in original_text)
        comparison = request(
            api, path + "/compare", {"features": [feature_payload("f1", paraphrase)]}
        )
        assert comparison["document_id"] == full["document_id"]
        assert comparison["evidence_embedding_digest"]
        [match] = comparison["items"]
        evidence = match["evidence"]
        assert match["evidence_method"] == "semantic" and evidence
        assert evidence["artifact_sha256"] == artifact_sha256
        assert verify_citation(evidence, detail, claims)
        print(
            f"{number}: semantic and hybrid rank 1; verified {evidence['kind']} citation"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", required=True)
    smoke(parser.parse_args().api)
