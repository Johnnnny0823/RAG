"""Measure the production retrieval SQL against an isolated official corpus."""

import argparse
import json
from datetime import UTC, datetime
from math import ceil
from pathlib import Path
from statistics import median

from services.api.db import engine
from services.api.patents import (
    PUBLIC_DOCUMENTS,
    SEMANTIC_SEARCH,
    GazettePdfQuery,
    RankedSearchRequest,
    gazette_pdf_statement,
    lexical_statement,
    search_filter_params,
    semantic_statement,
)
from services.retrieval.embeddings import LocalEmbeddingModel, model_id, vector_literal
from services.retrieval.fusion import CANDIDATE_LIMIT
from services.retrieval.lexical import TOKENIZER_VERSION, tokenize

CASES = (
    ("動態導通電阻", None),
    ("動態導通電阻", "G01R27/02"),
    ("光硬化性樹脂組成物", "C08F2/48"),
)
NODE_FIELDS = (
    "Node Type",
    "Relation Name",
    "Index Name",
    "Join Type",
    "Plan Rows",
    "Actual Rows",
    "Actual Loops",
    "Rows Removed by Filter",
    "Shared Hit Blocks",
    "Shared Read Blocks",
    "Temp Read Blocks",
    "Temp Written Blocks",
)


def summarize_plan(node: dict) -> dict:
    # Keep operator and cost evidence without SQL predicates or literal vectors.
    result = {key: node[key] for key in NODE_FIELDS if key in node}
    if "Plans" in node:
        result["Plans"] = [summarize_plan(child) for child in node["Plans"]]
    return result


def sample(conn, statement, repetitions: int) -> dict:
    sql, parameters = statement
    runs = []
    for index in range(repetitions + 1):
        measured = conn.exec_driver_sql(
            f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}", parameters
        ).scalar_one()[0]
        if index:
            runs.append(measured["Execution Time"])
    ordered = sorted(runs)
    return {
        "execution_ms": runs,
        "p50_ms": median(runs),
        "p95_ms": ordered[ceil(0.95 * len(ordered)) - 1],
        "last_planning_ms": measured["Planning Time"],
        "last_plan": summarize_plan(measured["Plan"]),
    }


def benchmark(repetitions: int) -> dict:
    model = LocalEmbeddingModel.from_env()
    queries = list(dict.fromkeys(query for query, _ in CASES))
    embeddings = dict(zip(queries, model.embed_queries(queries), strict=True))
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
        )
        corpus = f"(SELECT d.id {PUBLIC_DOCUMENTS})"
        identity = model_id(conn, model)
        if identity is None:
            raise ValueError("Configured model is not present in the isolated corpus")
        vectors = conn.exec_driver_sql(
            f"""SELECT count(*) FROM patent_dense_chunks t
                JOIN {corpus} c ON c.id = t.document_id WHERE t.model_id = %s""",
            (identity,),
        ).scalar_one()
        if not vectors:
            raise ValueError("Configured model has no indexed vectors")
        versions = conn.exec_driver_sql(
            f"SELECT count(*) {PUBLIC_DOCUMENTS}"
        ).scalar_one()
        chunks = conn.exec_driver_sql(
            f"""SELECT count(*) FROM patent_lexical_chunks t
                JOIN {corpus} c ON c.id = t.document_id
                WHERE t.tokenizer_version = %s AND t.field <> 'indexed'""",
            (TOKENIZER_VERSION,),
        ).scalar_one()
        if not versions or not chunks:
            raise ValueError(
                "The isolated corpus needs public documents and lexical chunks"
            )
        cases = []
        for query, ipc in CASES:
            filters = search_filter_params(RankedSearchRequest(query=query, ipc=ipc))
            vector = semantic_statement(
                vector_literal(embeddings[query]), identity, filters, CANDIDATE_LIMIT, 0
            )
            case = {
                "query": query,
                "ipc": ipc,
                "lexical": sample(
                    conn,
                    lexical_statement(
                        " & ".join(tokenize(query)), filters, CANDIDATE_LIMIT, 0
                    ),
                    repetitions,
                ),
                "vector": sample(conn, vector, repetitions),
            }
            if ipc is not None:
                reference = (SEMANTIC_SEARCH, vector[1])
                if (
                    conn.exec_driver_sql(*vector).all()
                    != conn.exec_driver_sql(*reference).all()
                ):
                    raise ValueError("IPC vector plan changed result rows or order")
                case["vector_reference"] = sample(conn, reference, repetitions)
                case["vector_reference_exact_match"] = True
            cases.append(case)
        return {
            "measured_at": datetime.now(UTC).isoformat(),
            "postgresql": conn.exec_driver_sql("SHOW server_version").scalar_one(),
            "pgvector": conn.exec_driver_sql(
                "SELECT extversion FROM pg_extension WHERE extname='vector'"
            ).scalar_one(),
            "documents": versions,
            "lexical_text_chunks": chunks,
            "vectors": vectors,
            "tokenizer": TOKENIZER_VERSION,
            "embedding_model": model.name,
            "embedding_digest": model.digest,
            "candidate_limit": CANDIDATE_LIMIT,
            "warmup_per_statement": 1,
            "cases": cases,
        }


def benchmark_gazette_pdf(repetitions: int) -> dict:
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
        )
        cases = []
        publication_pages = {("202640162", 1)}
        grant_pages = {("I941082", 1), ("I941082", 2)}
        for stage, expected in (
            (None, publication_pages | grant_pages),
            ("publication", publication_pages),
            ("grant", grant_pages),
        ):
            request = GazettePdfQuery(query="動態導通電阻", document_stage=stage)
            statement = gazette_pdf_statement(request)
            if statement is None:
                raise ValueError("The fixed gazette PDF query produced no terms")
            rows = conn.exec_driver_sql(*statement).mappings().all()
            actual = {(row["publication_no"], row["page_number"]) for row in rows}
            if actual != expected or len(rows) != len(expected):
                raise ValueError(
                    "Expected the isolated paired official gazette PDF fixture"
                )
            cases.append(
                {
                    "document_stage": stage,
                    "matching_pages": len(rows),
                    **sample(conn, statement, repetitions),
                }
            )
        return {
            "measured_at": datetime.now(UTC).isoformat(),
            "postgresql": conn.exec_driver_sql("SHOW server_version").scalar_one(),
            "query": "動態導通電阻",
            "warmup_per_statement": 1,
            "cases": cases,
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=7)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gazette-pdf", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.repetitions <= 30:
        parser.error("Repetitions must be between 1 and 30")
    if args.output.exists():
        parser.error("Output file already exists")
    measure = benchmark_gazette_pdf if args.gazette_pdf else benchmark
    result = measure(args.repetitions)
    with args.output.open("x", encoding="utf-8") as destination:
        json.dump(result, destination, ensure_ascii=False, indent=2)
        destination.write("\n")
