"""Measure actual Ollama calls for search using an isolated indexed corpus."""

import argparse
import json
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

from services.api.patents import (
    HybridSearchRequest,
    RankedSearchRequest,
    lexical_search,
    run_hybrid,
    semantic_search,
)
from services.retrieval.ollama import LocalOllamaModel


def token_count(body: dict, field: str) -> int | None:
    value = body.get(field)
    return value if type(value) is int and value >= 0 else None


def measure(query: str, repeats: int) -> list[dict]:
    request = RankedSearchRequest(query=query)
    hybrid = HybridSearchRequest(query=query)
    operations = {
        "lexical": lambda: lexical_search(request),
        "semantic": lambda: semantic_search(request),
        "hybrid": lambda: run_hybrid(hybrid),
        "hybrid_rerank": lambda: run_hybrid(hybrid.model_copy(update={"rerank": True})),
    }
    transport = LocalOllamaModel.request_json
    runs = []
    for mode, search in operations.items():
        for _ in range(repeats):
            calls = []

            def observe(model, path, payload=None, *, timeout=90):
                start = perf_counter()
                body = transport(model, path, payload, timeout=timeout)
                stats = body if isinstance(body, dict) else {}
                calls.append(
                    {
                        "endpoint": path,
                        "model": model.name,
                        "digest": model.digest,
                        "duration_ms": round((perf_counter() - start) * 1000, 2),
                        "prompt_tokens": token_count(stats, "prompt_eval_count"),
                        "generated_tokens": token_count(stats, "eval_count"),
                    }
                )
                return body

            with patch.object(LocalOllamaModel, "request_json", observe):
                started = perf_counter()
                result = search()
                elapsed = perf_counter() - started
            if not hasattr(result, "items") or not result.items:
                raise ValueError(f"{mode} did not return indexed candidates")
            if mode == "hybrid_rerank" and result.reranker is None:
                raise ValueError(
                    "The fixture must return multiple candidates to exercise reranking"
                )
            runs.append(
                {
                    "mode": mode,
                    "elapsed_ms": round(elapsed * 1000, 2),
                    "candidates": len(result.items),
                    "calls": calls,
                }
            )
    return runs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="動態導通電阻")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 20:
        parser.error("--repeats must be between 1 and 20")
    if args.output.exists():
        parser.error("Output already exists")
    try:
        runs = measure(args.query, args.repeats)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump({"runs": runs}, output, indent=2, ensure_ascii=False)
            output.write("\n")
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(f"Measured {len(runs)} searches across four modes")


if __name__ == "__main__":
    main()
