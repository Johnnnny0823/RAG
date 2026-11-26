"""Authenticated queue for saving a background patent search."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Response
from psycopg.types.json import Jsonb
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from services.api.db import engine
from services.api.audit import record_audit_event
from services.api.patents import (
    HybridSearchRequest,
    PatentErrorEnvelope,
    PatentRoute,
    api_error,
    search_filter_params,
    unavailable,
)
from services.api.search_runs import Owner

router = APIRouter(
    prefix="/api/v1/search-jobs",
    tags=["research"],
    route_class=PatentRoute,
    responses={
        status: {"model": PatentErrorEnvelope} for status in (401, 404, 409, 422, 503)
    },
)

STATUS_COLUMNS = "id, status, run_id, error_code, created_at, started_at, finished_at"


class SearchJob(BaseModel):
    id: UUID
    status: Literal["queued", "running", "succeeded", "failed", "cancelled"]
    run_id: UUID | None
    error_code: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


def public_status(row, response: Response):
    if row is None:
        return api_error(404, "SEARCH_JOB_NOT_FOUND", "找不到此搜尋工作。")
    response.headers["Cache-Control"] = "no-store"
    return SearchJob.model_validate(row)


@router.post("", response_model=SearchJob, status_code=202)
def enqueue(request: HybridSearchRequest, account: Owner, response: Response):
    if not request.query.strip():
        return api_error(422, "INVALID_REQUEST", "請提供可檢索的文字。")
    if len({feature.feature_id for feature in request.features}) != len(
        request.features
    ):
        return api_error(422, "INVALID_REQUEST", "技術特徵 ID 必須唯一。")
    try:
        search_filter_params(request)
    except ValueError as error:
        return api_error(422, "INVALID_REQUEST", str(error))
    try:
        with engine.begin() as conn:
            row = (
                conn.exec_driver_sql(
                    f"""INSERT INTO search_jobs (user_id, request) VALUES (%s, %s)
                    ON CONFLICT DO NOTHING RETURNING {STATUS_COLUMNS}""",
                    (account.id, Jsonb(request.model_dump(mode="json"))),
                )
                .mappings()
                .one_or_none()
            )
    except SQLAlchemyError:
        return unavailable()
    if row is None:
        return api_error(409, "SEARCH_JOB_ACTIVE", "已有一項搜尋工作正在等待或執行。")
    response.headers["Location"] = f"/api/v1/search-jobs/{row['id']}"
    record_audit_event(
        "enqueue", "search_job", user_id=account.id, resource_id=row["id"]
    )
    return public_status(row, response)


@router.get("/active", response_model=SearchJob | None)
def active_job(account: Owner, response: Response):
    try:
        with engine.connect() as conn:
            row = (
                conn.exec_driver_sql(
                    f"""SELECT {STATUS_COLUMNS} FROM search_jobs
                    WHERE user_id = %s AND status IN ('queued', 'running')""",
                    (account.id,),
                )
                .mappings()
                .one_or_none()
            )
    except SQLAlchemyError:
        return unavailable()
    response.headers["Cache-Control"] = "no-store"
    return SearchJob.model_validate(row) if row is not None else None


@router.get("/{job_id}", response_model=SearchJob)
def job_status(job_id: UUID, account: Owner, response: Response):
    try:
        with engine.connect() as conn:
            row = (
                conn.exec_driver_sql(
                    f"SELECT {STATUS_COLUMNS} FROM search_jobs WHERE id = %s AND user_id = %s",
                    (job_id, account.id),
                )
                .mappings()
                .one_or_none()
            )
    except SQLAlchemyError:
        return unavailable()
    return public_status(row, response)


@router.post("/{job_id}/cancel", response_model=SearchJob)
def cancel(job_id: UUID, account: Owner, response: Response):
    try:
        with engine.begin() as conn:
            row = (
                conn.exec_driver_sql(
                    f"""UPDATE search_jobs
                    SET status = 'cancelled', request = NULL, finished_at = now()
                    WHERE id = %s AND user_id = %s AND status IN ('queued', 'running')
                    RETURNING {STATUS_COLUMNS}""",
                    (job_id, account.id),
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                row = (
                    conn.exec_driver_sql(
                        f"SELECT {STATUS_COLUMNS} FROM search_jobs WHERE id = %s AND user_id = %s",
                        (job_id, account.id),
                    )
                    .mappings()
                    .one_or_none()
                )
    except SQLAlchemyError:
        return unavailable()
    return public_status(row, response)
