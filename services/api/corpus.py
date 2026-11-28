"""Read-only official corpus coverage and ingestion batch status endpoint."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Response
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from services.api.db import engine
from services.api.patents import PatentErrorEnvelope, PatentRoute, unavailable

router = APIRouter(
    prefix="/api/v1/corpus",
    tags=["corpus"],
    route_class=PatentRoute,
    responses={503: {"model": PatentErrorEnvelope}},
)


class IngestionBatchSummary(BaseModel):
    dataset_key: str
    batch_key: str
    parser_version: str
    status: str
    counts: dict[str, Any] = Field(default_factory=dict)
    finished_at: datetime | None


class CorpusStatus(BaseModel):
    datasets_count: int
    documents_total: int
    publications_count: int
    grants_count: int
    lexical_indexed_documents: int
    semantic_indexed_documents: int
    latest_ingested_at: datetime | None
    recent_batches: list[IngestionBatchSummary]


CORPUS_SUMMARY_SQL = """
    WITH official_docs AS (
        SELECT DISTINCT d.id, d.document_stage
        FROM patent_documents d
        JOIN document_artifacts da ON da.document_id = d.id
        JOIN ingestion_artifacts ia ON ia.id = da.artifact_id
        JOIN ingestion_batches b ON b.id = ia.batch_id
        JOIN source_datasets s ON s.id = b.dataset_id
        WHERE d.jurisdiction = 'TW'
          AND NOT s.is_demo
          AND ia.status IN ('parsed', 'partial')
          AND b.status IN ('complete', 'partial')
    )
    SELECT
        (SELECT count(*) FROM source_datasets WHERE NOT is_demo) AS datasets_count,
        (SELECT count(*) FROM official_docs) AS documents_total,
        (SELECT count(*) FROM official_docs WHERE document_stage = 'publication') AS publications_count,
        (SELECT count(*) FROM official_docs WHERE document_stage = 'grant') AS grants_count,
        (
            SELECT count(DISTINCT c.document_id)
            FROM patent_lexical_chunks c
            JOIN official_docs d ON d.id = c.document_id
        ) AS lexical_indexed_documents,
        (
            SELECT count(DISTINCT c.document_id)
            FROM patent_dense_chunks c
            JOIN official_docs d ON d.id = c.document_id
        ) AS semantic_indexed_documents,
        (
            SELECT max(b.finished_at)
            FROM ingestion_batches b
            JOIN source_datasets s ON s.id = b.dataset_id
            WHERE NOT s.is_demo AND b.status IN ('complete', 'partial')
        ) AS latest_ingested_at
"""

RECENT_BATCHES_SQL = """
    SELECT
        s.dataset_key,
        b.batch_key,
        b.parser_version,
        b.status,
        b.counts_jsonb AS counts,
        b.finished_at
    FROM ingestion_batches b
    JOIN source_datasets s ON s.id = b.dataset_id
    WHERE NOT s.is_demo
    ORDER BY COALESCE(b.finished_at, b.started_at) DESC, b.id DESC
    LIMIT 10
"""


def fetch_corpus_status() -> CorpusStatus:
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn:
        summary = conn.exec_driver_sql(CORPUS_SUMMARY_SQL).mappings().one()
        batches = conn.exec_driver_sql(RECENT_BATCHES_SQL).mappings().all()
    return CorpusStatus(
        datasets_count=int(summary["datasets_count"] or 0),
        documents_total=int(summary["documents_total"] or 0),
        publications_count=int(summary["publications_count"] or 0),
        grants_count=int(summary["grants_count"] or 0),
        lexical_indexed_documents=int(summary["lexical_indexed_documents"] or 0),
        semantic_indexed_documents=int(summary["semantic_indexed_documents"] or 0),
        latest_ingested_at=summary["latest_ingested_at"],
        recent_batches=[
            IngestionBatchSummary.model_validate(
                {
                    **row,
                    "counts": {
                        key: count
                        for key, count in (row["counts"] or {}).items()
                        if key
                        in {
                            "metadata",
                            "fulltext",
                            "grants_with_claims",
                            "invention_events",
                            "matched_events",
                        }
                        and type(count) is int
                        and count >= 0
                    },
                }
            )
            for row in batches
        ],
    )


@router.get("/status", response_model=CorpusStatus)
def corpus_status(response: Response):
    try:
        status = fetch_corpus_status()
    except SQLAlchemyError:
        return unavailable()
    response.headers["Cache-Control"] = "no-store"
    return status
