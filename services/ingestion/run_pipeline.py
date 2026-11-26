"""Run an operator-authorized official import and optional corpus indexing."""

import argparse
import re
from argparse import Namespace
from uuid import UUID

from psycopg.types.json import Jsonb

from services.api.db import engine
from services.ingestion.import_issue import import_issue, parse_import_args
from services.retrieval.embeddings import LocalEmbeddingModel
from services.retrieval.index_lexical import index_missing as index_lexical
from services.retrieval.index_semantic import index_missing as index_semantic

PIPELINE_LOCK = 920502


def checkpoint(job_id: UUID, stage: str, counts: dict, status: str = "running") -> None:
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """UPDATE ingestion_jobs SET stage = %s, counts = %s, status = %s,
                      updated_at = now(),
                      finished_at = CASE WHEN %s = 'running' THEN NULL ELSE now() END
               WHERE id = %s""",
            (stage, Jsonb(counts), status, status, job_id),
        )


def run_pipeline(
    args: Namespace,
    index_mode: str,
    batch_size: int,
    timeout: int,
    *,
    require_complete: bool = False,
) -> int:
    with engine.connect() as lock:
        if not lock.exec_driver_sql(
            "SELECT pg_try_advisory_lock(%s)", (PIPELINE_LOCK,)
        ).scalar_one():
            raise SystemExit("Another tracked ingestion pipeline owns the lock")
        lock.commit()
        with engine.begin() as conn:
            conn.exec_driver_sql(
                """UPDATE ingestion_jobs SET status = 'interrupted', updated_at = now(),
                          finished_at = now() WHERE status = 'running'"""
            )
            job_id = conn.exec_driver_sql(
                "INSERT INTO ingestion_jobs (batch_key) VALUES (%s) RETURNING id",
                (args.batch,),
            ).scalar_one()
        print(f"Ingestion job {job_id}", flush=True)
        counts = {}
        stage = "import"
        try:
            imported = import_issue(args)
            counts["import"] = {
                key: imported[key]
                for key in (
                    "fulltext",
                    "metadata",
                    "invalid_records",
                    "quarantined_specs",
                    "grants_with_claims",
                    "legal_events_linked",
                    "reused",
                )
                if key in imported
            }
            counts["import"]["download_failures"] = len(
                imported.get("download_failures", [])
            )
            result = imported["status"]
            if result != "failed" and index_mode != "none":
                stage = "lexical"
                checkpoint(job_id, stage, counts)
                versions, chunks = index_lexical(20)
                counts["lexical"] = {"versions": versions, "chunks": chunks}
            if result != "failed" and index_mode == "hybrid":
                stage = "semantic"
                checkpoint(job_id, stage, counts)
                versions, vectors = index_semantic(
                    LocalEmbeddingModel.from_env(),
                    batch_size=batch_size,
                    request_timeout=timeout,
                )
                counts["semantic"] = {"versions": versions, "vectors": vectors}
        except KeyboardInterrupt:
            checkpoint(job_id, stage, counts, "interrupted")
            return 130
        except Exception as error:
            checkpoint(job_id, stage, counts, "failed")
            print(
                f"Ingestion job {job_id} failed at {stage} ({type(error).__name__})",
                flush=True,
            )
            return 1
        status = {"complete": "succeeded", "partial": "partial", "failed": "failed"}[
            result
        ]
        checkpoint(job_id, stage, counts, status)
        print(f"Ingestion job {job_id}: {status}", flush=True)
        return int(status == "failed" or (require_complete and status == "partial"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--index-mode", choices=["none", "lexical", "hybrid"], default="lexical"
    )
    parser.add_argument("--embedding-batch-size", type=int, default=24)
    parser.add_argument("--embedding-timeout", type=int, default=90)
    parser.add_argument("import_options", nargs=argparse.REMAINDER)
    options = parser.parse_args()
    if (
        not 1 <= options.embedding_batch_size <= 24
        or not 1 <= options.embedding_timeout <= 1800
    ):
        parser.error(
            "Embedding batch size must be 1..24 and timeout must be 1..1800 seconds"
        )
    args = parse_import_args(
        options.import_options[1:]
        if options.import_options[:1] == ["--"]
        else options.import_options
    )
    if (
        not args.verified_tipo
        or not args.index_source_url
        or args.fetch_only
        or not re.fullmatch(r"[0-9]{6}", args.batch)
    ):
        parser.error(
            "A verified official issue import with a six-digit batch is required"
        )
    raise SystemExit(
        run_pipeline(
            args,
            options.index_mode,
            options.embedding_batch_size,
            options.embedding_timeout,
        )
    )
