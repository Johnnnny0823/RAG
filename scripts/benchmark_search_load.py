"""Measure closed-loop search latency against an isolated local official corpus."""

import argparse
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from math import ceil
from pathlib import Path
from statistics import median
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MODES = {"lexical": "", "semantic": "/semantic", "hybrid": "/hybrid"}
PARALLELISM = (1, 2, 4)
REQUEST_BODY = {
    "query": "動態導通電阻",
    "ipc": "G01R27/02",
    "limit": 10,
}
EXPECTED_DOCUMENT = ("publication", "202640162")


def measure_request(url: str, *, metadata: dict | None = None) -> tuple[str, float]:
    req = Request(
        url,
        data=json.dumps(REQUEST_BODY).encode(),
        headers={"Content-Type": "application/json"},
    )
    start = perf_counter()
    try:
        with urlopen(req, timeout=30) as response:
            payload = json.load(response)
        items = payload["items"]
        known_item = EXPECTED_DOCUMENT in {
            (item["document_stage"], item["publication_no"]) for item in items
        }
        outcome = "200_known_item" if known_item else "200_missing_known_item"
        if metadata is not None:
            metadata.update(
                (key, payload[key])
                for key in (
                    "tokenizer_version",
                    "model_name",
                    "model_digest",
                    "pipeline",
                    "query_expansion_version",
                    "corpus_coverage",
                )
                if key in payload
            )
    except HTTPError as error:
        with error:
            outcome = f"http_{error.code}"
            if error.code == 429:
                try:
                    code = json.load(error).get("error", {}).get("code")
                except ValueError:
                    code = None
                if code == "MODEL_BUSY":
                    outcome = "429_model_busy"
    except (URLError, TimeoutError):
        outcome = "transport_error"
    except (KeyError, TypeError, ValueError):
        outcome = "invalid_response"
    return outcome, (perf_counter() - start) * 1000


def summarize(results: list[tuple[str, float]], wall_seconds: float) -> dict:
    outcomes = dict(Counter(outcome for outcome, _ in results))
    successful = sorted(
        latency for outcome, latency in results if outcome == "200_known_item"
    )
    return {
        "requests": len(results),
        "outcomes": outcomes,
        "success_per_second": round(len(successful) / wall_seconds, 3),
        "successful_p50_ms": round(median(successful), 2) if successful else None,
        "successful_p95_ms": round(successful[ceil(0.95 * len(successful)) - 1], 2)
        if successful
        else None,
    }


def benchmark(api: str, requests: int) -> dict:
    # Keep this acceptance workload on the explicitly chosen loopback test instance.
    if not re.fullmatch(r"http://127\.0\.0\.1:[0-9]{1,5}", api):
        raise ValueError("Use a loopback test API URL, e.g. http://127.0.0.1:18039")
    groups = []
    warmup_metadata = {}
    measured_at = datetime.now(UTC).isoformat()
    for mode, suffix in MODES.items():
        url = f"{api}/api/v1/patents/search{suffix}"
        metadata = warmup_metadata[mode] = {}
        warmup, _ = measure_request(url, metadata=metadata)
        if warmup != "200_known_item":
            raise ValueError(f"{mode} warmup failed: {warmup}")
        for workers in PARALLELISM:
            start = perf_counter()
            with ThreadPoolExecutor(max_workers=workers) as pool:
                results = list(pool.map(measure_request, [url] * requests))
            groups.append(
                {
                    "mode": mode,
                    "concurrency": workers,
                    **summarize(results, perf_counter() - start),
                }
            )
    return {
        "measured_at": measured_at,
        "request_body": REQUEST_BODY,
        "expected_document": EXPECTED_DOCUMENT,
        "reranking": False,
        "warmup_metadata": warmup_metadata,
        "groups": groups,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", required=True)
    parser.add_argument("--requests-per-group", type=int, default=12)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 8 <= args.requests_per_group <= 100:
        parser.error("Requests per group must be from 8 through 100")
    if args.output.exists():
        parser.error("Output file already exists")
    result = benchmark(args.api, args.requests_per_group)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.write("\n")
    if any(
        not group["outcomes"].get("200_known_item")
        or group["outcomes"].keys() - {"200_known_item", "429_model_busy"}
        for group in result["groups"]
    ):
        parser.exit(1, f"Unexpected outcomes recorded in {args.output}\n")


if __name__ == "__main__":
    main()
