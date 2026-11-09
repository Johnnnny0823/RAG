"""Verify comparison citations across official documents and coverage levels."""

import argparse
import json
from urllib.parse import urlencode

from evaluate_search import request

CASES = (
    ("publication", "202640162", "fulltext", "動態導通電阻量測電路", "claim"),
    ("grant", "I941082", "claims_only", "動態導通電阻量測電路", "claim"),
    ("publication", "202639611", "fulltext", "光硬化性樹脂組成物", "claim"),
    (
        "publication",
        "202639611",
        "fulltext",
        "可將長波長光轉換為短波長光",
        "disclosure",
    ),
    ("publication", "202639448", "fulltext", "廢水自動監控及添加系統", "claim"),
    ("publication", "202640537", "fulltext", "根據解剖影像辨識人體輪廓", "claim"),
    ("publication", "202640162", "metadata_and_abstract", "動態導通電阻量測電路", None),
)
ABSENT = "不存在的驗收字串甲乙丙丁"
POSITIVE = {"supported", "partially_supported"}


def verify_citation(citation, detail, claims):
    kind = citation["kind"]
    ordinal = citation["ordinal"]
    if kind == "claim":
        rows = [
            (row["text"], row["source"])
            for row in claims
            if row["claim_number"] == ordinal
        ]
    else:
        rows = [
            (row["original_text"], row["source"])
            for row in detail["sections"]
            if row["section_type"] == kind and row["ordinal"] == ordinal
        ]
    start, end = citation["char_start"], citation["char_end"]
    checksum = citation["artifact_sha256"]
    return any(
        source["artifact_sha256"] == checksum for source in detail["sources"]
    ) and any(
        source["artifact_sha256"] == checksum
        and source["xpath"] == citation["xpath"]
        and 0 <= start < end <= len(text)
        and text[start:end] == citation["quote"]
        for text, source in rows
    )


def evaluate(api):
    results = []
    document_ids = set()
    for stage, number, scope, query, expected_kind in CASES:
        params = urlencode({"number": number, "number_type": stage})
        items = request(api, "/patents?" + params)["items"]
        document = next(item for item in items if item["content_scope"] == scope)
        document_ids.add(document["document_id"])
        path = "/patents/" + document["document_id"]
        detail = request(api, path)
        claims = request(api, path + "/claims")["claims"]
        if expected_kind == "disclosure" and (
            any(query in row["text"] for row in claims)
            or not any(
                row["section_type"] == expected_kind and query in row["original_text"]
                for row in detail["sections"]
            )
        ):
            raise ValueError(
                f"Section-only fixture does not match the indexed source: {number}"
            )
        features = [
            {
                "feature_id": feature_id,
                "description_zh": text,
                "keywords_zh": [],
                "keywords_en": [],
                "must_have": True,
                "confidence": "high",
                "ipc_candidates": [],
            }
            for feature_id, text in (("f1", query), ("f2", ABSENT))
        ]
        comparison = request(api, path + "/compare", {"features": features})
        if (
            comparison["document_id"] != detail["document_id"]
            or comparison["document_sha256"] != detail["document_sha256"]
        ):
            raise ValueError(f"Comparison source version mismatch: {number}/{scope}")
        judgments = {item["feature_id"]: item for item in comparison["items"]}
        if len(comparison["items"]) != len(features) or judgments.keys() != {
            "f1",
            "f2",
        }:
            raise ValueError(
                f"Comparison returned unexpected features: {number}/{scope}"
            )
        for feature_id, item in judgments.items():
            citation = item["evidence"]
            results.append(
                {
                    "number": number,
                    "scope": scope,
                    "document_id": document["document_id"],
                    "feature_id": feature_id,
                    "query": query if feature_id == "f1" else ABSENT,
                    "verdict": item["verdict"],
                    "citation_present": citation is not None,
                    "citation_kind": citation["kind"] if citation else None,
                    "citation_verified": verify_citation(citation, detail, claims)
                    if citation
                    else None,
                    "model_digest": comparison["model_digest"],
                }
            )
        expected_no_evidence = (
            "uncertain"
            if scope == "metadata_and_abstract"
            else "not_found_in_checked_content"
        )
        if (
            judgments["f2"]["evidence"]
            or judgments["f2"]["verdict"] != expected_no_evidence
        ):
            raise ValueError(f"Missing-evidence case failed: {number}/{scope}")
        if scope == "metadata_and_abstract" and (
            judgments["f1"]["evidence"] or judgments["f1"]["verdict"] != "uncertain"
        ):
            raise ValueError(f"Metadata-only version must be uncertain: {number}")
        evidence = judgments["f1"]["evidence"]
        if expected_kind is not None and (
            evidence is None
            or evidence["kind"] != expected_kind
            or judgments["f1"]["verdict"] not in POSITIVE
        ):
            raise ValueError(
                f"Expected {expected_kind} citation not returned: {number}/{query}"
            )

    emitted = [row for row in results if row["citation_present"]]
    verified = sum(row["citation_verified"] for row in emitted)
    positive_without_citation = sum(
        row["verdict"] in POSITIVE and not row["citation_present"] for row in results
    )
    return {
        "comparison_requests": len(CASES),
        "document_versions": len(document_ids),
        "feature_verdicts": len(results),
        "citations_emitted": len(emitted),
        "citations_verified": verified,
        "citation_exactness": verified / len(emitted) if emitted else None,
        "positive_without_citation": positive_without_citation,
        "expected_evidence_cases_without_citation": sum(
            row["feature_id"] == "f1"
            and row["scope"] != "metadata_and_abstract"
            and not row["citation_present"]
            for row in results
        ),
        "results": results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:18022")
    result = evaluate(parser.parse_args().api)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["citation_exactness"] != 1 or result["positive_without_citation"]:
        raise SystemExit(1)
