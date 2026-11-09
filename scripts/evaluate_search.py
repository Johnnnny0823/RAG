"""Measure retrieval modes against a versioned TIPO relevance pool."""

import argparse
import json
import math
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


def evaluate(api, dataset, repeats):
    if not dataset["cases"]:
        raise ValueError("Evaluation dataset must contain at least one case")
    modes = {mode: [] for mode in MODES}
    for case in dataset["cases"]:
        judgments = case["judgments"]
        labels = {(row["stage"], row["number"]): row["grade"] for row in judgments}
        if (
            len(labels) != len(judgments)
            or not any(labels.values())
            or not all(grade in (0, 1, 2) for grade in labels.values())
        ):
            raise ValueError(f"Invalid or duplicate judgments for {case['id']}")
        for stage, number in labels:
            params = urlencode({"number": number, "number_type": stage})
            if not request(api, "/patents?" + params)["items"]:
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:18017")
    parser.add_argument(
        "--dataset", type=Path, default=Path("evaluation/tipo_seed.json")
    )
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    print(
        json.dumps(
            evaluate(args.api, dataset, args.repeats), ensure_ascii=False, indent=2
        )
    )
