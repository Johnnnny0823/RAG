"""Read-only ingestion monitoring for operator-selected account IDs."""

import os
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Response
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from services.api.db import engine
from services.api.patents import (
    PatentErrorEnvelope,
    PatentRoute,
    api_error,
    unavailable,
)
from services.api.search_runs import Owner

router = APIRouter(
    prefix="/api/v1/admin/ingestion",
    tags=["admin"],
    route_class=PatentRoute,
    responses={
        status: {"model": PatentErrorEnvelope} for status in (401, 403, 422, 503)
    },
)


def is_ingestion_admin(user_id: UUID) -> bool:
    return str(user_id) in {
        item.strip().lower()
        for item in os.getenv("INGESTION_ADMIN_USER_IDS", "").split(",")
    }


class IngestionJob(BaseModel):
    id: UUID
    batch_key: str
    status: Literal["running", "succeeded", "partial", "failed", "interrupted"]
    stage: Literal["import", "lexical", "semantic"]
    counts: dict[str, dict[str, bool | int]]
    started_at: datetime
    updated_at: datetime
    finished_at: datetime | None


@router.get("/jobs", response_model=list[IngestionJob])
def list_ingestion_jobs(
    account: Owner,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
):
    if not is_ingestion_admin(account.id):
        return api_error(403, "ADMIN_REQUIRED", "此功能僅限匯入管理員。")
    try:
        with engine.connect() as conn:
            rows = (
                conn.exec_driver_sql(
                    """SELECT id, batch_key, status, stage, counts, started_at, updated_at, finished_at
                   FROM ingestion_jobs ORDER BY started_at DESC, id LIMIT %s OFFSET %s""",
                    (limit, offset),
                )
                .mappings()
                .all()
            )
    except SQLAlchemyError:
        return unavailable()
    response.headers["Cache-Control"] = "private, no-store"
    return [IngestionJob.model_validate(row) for row in rows]
