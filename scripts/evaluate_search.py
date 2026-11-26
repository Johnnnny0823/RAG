"""Measure retrieval modes against a versioned TIPO relevance pool."""

import argparse
import json
import math
import re
from pathlib import Path
from statistics import mean, median
from time import perf_counter
from urllib.parse import urlencode
from urllib.request import Request, urlopen

MODES = {
    "lexical": ("", {}),
    "semantic": ("/semantic", {}),
    "hybrid_rerank": ("/hybrid", {"rerank": True}),
}
K = 10
SCOPES = {"metadata_and_abstract": 0, "claims_only": 1, "fulltext": 2}
VERSION_FIELDS = ("content_scope", "document_sha256", "parser_version")


def request(api, path, payload=None):
    req = Request(
        api.rstrip("/") + "/api/v1" + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(req, timeout=180) as response:
        return json.load(response)


def score(items, labels):
    # Alternate versions of one publication consume their original rank.
    # Only the first occurrence earns credit.
    seen = set()
    grades = []
    judged = 0
    for item in items[:K]:
        key = (item["document_stage"], item["publication_no"])
        judged += key in labels
        grades.append(labels.get(key, 0) if key not in seen else 0)
        seen.add(key)
    matched = sum(grade > 0 for grade in grades)
    ideal = sorted(labels.values(), reverse=True)[:K]

    def dcg(values):
        return sum(
            (2**value - 1) / math.log2(rank + 1) for rank, value in enumerate(values, 1)
        )

    return {
        "precision_at_10_lower_bound": matched / K,
        "recall_at_10_relative_to_pool": matched
        / sum(grade > 0 for grade in labels.values()),
        "ndcg_at_10_relative_to_pool": dcg(grades) / dcg(ideal),
        "reciprocal_rank": next(
            (1 / rank for rank, grade in enumerate(grades, 1) if grade), 0
        ),
        "unjudged_returned": len(grades) - judged,
    }


def version_details(api, stage, number):
    offset = 0
    while True:
        params = urlencode(
            {"number": number, "number_type": stage, "limit": 100, "offset": offset}
        )
        result = request(api, "/patents?" + params)
        for version in result["items"]:
            yield version
        if not result["has_more"]:
            break
        offset += len(result["items"])


def check_reviewed_version(api, row, versions):
    if (
        row.get("content_scope") not in SCOPES
        or not re.fullmatch(r"[0-9a-f]{64}", row.get("document_sha256") or "")
        or not (row.get("parser_version") or "").strip()
    ):
        raise ValueError("Human-reviewed judgments require a pinned document version")
    for version in versions:
        if version["content_scope"] == row["content_scope"]:
            detail = request(api, "/patents/" + version["document_id"])
            if all(detail[field] == row[field] for field in VERSION_FIELDS):
                return detail
    raise ValueError(f"Reviewed version missing: {row['stage']}/{row['number']}")


def evaluate(api, dataset, repeats):
    if not dataset["cases"]:
        raise ValueError("Evaluation dataset must contain at least one case")
    if repeats < 1:
        raise ValueError("Evaluation requires at least one repeat")
    if len({case["id"] for case in dataset["cases"]}) != len(dataset["cases"]):
        raise ValueError("Evaluation case IDs must be unique")
    human_reviewed = dataset["label_status"] == "human_reviewed"
    if dataset["label_status"] == "pending_human_review":
        raise ValueError("The review pool is still pending human review")
    if human_reviewed and not dataset.get("reviewer", "").strip():
        raise ValueError("Human-reviewed datasets require a reviewer")
    modes = {mode: [] for mode in MODES}
    for case in dataset["cases"]:
        judgments = case["judgments"]
        if human_reviewed and any(
            not row.get("basis", "").strip() for row in judgments
        ):
            raise ValueError(f"Human-reviewed judgments require a basis: {case['id']}")
        labels = {(row["stage"], row["number"]): row["grade"] for row in judgments}
        if (
            len(labels) != len(judgments)
            or not any(labels.values())
            or not all(
                type(grade) is int and 0 <= grade <= 2 for grade in labels.values()
            )
        ):
            raise ValueError(f"Invalid or duplicate judgments for {case['id']}")
        for row in judgments:
            stage, number = row["stage"], row["number"]
            versions = version_details(api, stage, number)
            if human_reviewed:
                check_reviewed_version(api, row, versions)
            elif next(versions, None) is None:
                raise ValueError(
                    f"Required evaluation document missing: {stage}/{number}"
                )
        payload = {"query": case["query"], "ipc": case.get("ipc"), "limit": K}
        for mode, (suffix, options) in MODES.items():
            for _ in range(repeats):
                started = perf_counter()
                data = request(api, "/patents/search" + suffix, {**payload, **options})
                latency = round((perf_counter() - started) * 1000, 2)
                items = data.pop("items")
                modes[mode].append(
                    {
                        "case": case["id"],
                        "latency_ms": latency,
                        "metrics": score(items, labels),
                        "results": [
                            {
                                field: item[field]
                                for field in (
                                    "document_id",
                                    "publication_no",
                                    "document_stage",
                                    "content_scope",
                                )
                            }
                            for item in items
                        ],
                        "search_metadata": data,
                    }
                )
    summary = {}
    for mode, runs in modes.items():
        times = sorted(run["latency_ms"] for run in runs)
        summary[mode] = {
            "runs": len(times),
            "p50_ms": median(times),
            "p95_ms_nearest_rank": times[math.ceil(0.95 * len(times)) - 1],
            **{
                key: mean(run["metrics"][key] for run in runs)
                for key in runs[0]["metrics"]
            },
        }
    return {"label_status": dataset["label_status"], "summary": summary, "runs": modes}


def build_review_pool(api, dataset, evaluation):
    candidates = {case["id"]: set() for case in dataset["cases"]}
    for runs in evaluation["runs"].values():
        for run in runs:
            pool = candidates[run["case"]]
            pool.update(
                (hit["document_stage"], hit["publication_no"]) for hit in run["results"]
            )

    cases = []
    documents = {}
    for case in dataset["cases"]:
        pool = candidates[case["id"]]
        pool.update((row["stage"], row["number"]) for row in case["judgments"])
        rows = []
        for stage, number in sorted(pool):
            key = (stage, number)
            if key not in documents:
                versions = list(version_details(api, stage, number))
                if not versions:
                    raise ValueError(f"Candidate document missing: {stage}/{number}")
                scope = max(SCOPES[version["content_scope"]] for version in versions)
                details = (
                    request(api, "/patents/" + version["document_id"])
                    for version in versions
                    if SCOPES[version["content_scope"]] == scope
                )
                documents[key] = min(
                    details,
                    key=lambda detail: (
                        detail["document_sha256"],
                        detail["parser_version"],
                    ),
                )
            detail = documents[key]
            urls = {
                url
                for source in detail["sources"]
                for url in (source["source_url"], source["dataset_url"])
                if url
            }
            rows.append(
                {
                    "stage": stage,
                    "number": number,
                    "title": detail["title_zh"] or detail["title_en"],
                    "document_id": detail["document_id"],
                    **{field: detail[field] for field in VERSION_FIELDS},
                    "official_sources": sorted(urls),
                    "grade": None,
                    "basis": "",
                }
            )
        cases.append(
            {
                "id": case["id"],
                "query": case["query"],
                "ipc": case.get("ipc"),
                "judgments": rows,
            }
        )
    return {"label_status": "pending_human_review", "reviewer": "", "cases": cases}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:18017")
    parser.add_argument(
        "--dataset", type=Path, default=Path("evaluation/tipo_seed.json")
    )
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument(
        "--review-pool", type=Path, help="Write a new rank-blind human review dataset"
    )
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    result = evaluate(args.api, dataset, args.repeats)
    if args.review_pool:
        pool = build_review_pool(args.api, dataset, result)
        with args.review_pool.open("x", encoding="utf-8") as file:
            json.dump(pool, file, ensure_ascii=False, indent=2)
            file.write("\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
