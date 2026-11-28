"""Verify searchable and citable grant versions from the official 053030 issue."""

import argparse

from evaluate_citations import POSITIVE, feature_payload, verify_citation
from evaluate_search import request

CASES = (
    ("I942741", "G02B5/30", "偏光板", "多層偏光元件用於顯示裝置", "透明保護層"),
    (
        "I942850",
        "H01G9/035",
        "電解電容器",
        "將含碳層的陰極箔用於電解式電容元件",
        "電介質氧化皮膜",
    ),
)


def smoke(api):
    for number, ipc, term, paraphrase, feature in CASES:
        items = request(api, f"/patents?number={number}&number_type=grant")["items"]
        versions = {item["content_scope"]: item for item in items}
        assert {"fulltext", "claims_only"} <= versions.keys()
        assert (
            versions["fulltext"]["application_no"]
            == versions["claims_only"]["application_no"]
        )
        for coverage in ("fulltext", "claims_only"):
            expected = versions[coverage]["document_id"]
            common = {
                "ipc": ipc,
                "document_stage": "grant",
                "content_scope": coverage,
            }
            for route, query in (
                ("/patents/search", term),
                ("/patents/search/semantic", paraphrase),
                ("/patents/search/hybrid", paraphrase),
            ):
                result = request(api, route, {**common, "query": query})
                assert any(item["document_id"] == expected for item in result["items"])
                assert all(
                    item["document_stage"] == "grant"
                    and item["content_scope"] == coverage
                    for item in result["items"]
                )
                if route.endswith("/hybrid"):
                    assert result["corpus_coverage"]["lexical_versions"] >= 1
                    assert result["corpus_coverage"]["semantic_versions"] >= 1

        full = "/patents/" + versions["fulltext"]["document_id"]
        claims_only = "/patents/" + versions["claims_only"]["document_id"]
        detail = request(api, full)
        claims = request(api, full + "/claims")["claims"]
        index_claims = request(api, claims_only + "/claims")["claims"]
        archive_hashes = {item["source"]["artifact_sha256"] for item in index_claims}
        result = request(
            api,
            full + "/compare",
            {"features": [feature_payload("f1", feature)], "semantic_evidence": False},
        )
        assert result["document_id"] == detail["document_id"]
        assert result["document_sha256"] == detail["document_sha256"]
        [match] = result["items"]
        evidence = match["evidence"]
        assert match["verdict"] in POSITIVE and evidence
        assert evidence["artifact_sha256"] not in archive_hashes
        assert verify_citation(evidence, detail, claims)
        print(
            f"{number}: filtered lexical, semantic and hybrid retrieval; fulltext citation verified"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", required=True)
    smoke(parser.parse_args().api)
