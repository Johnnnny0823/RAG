"""Background PDF requests, with ownership inherited from the saved search."""

import logging
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Response
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from services.api.db import engine
from services.api.patents import (
    PatentErrorEnvelope,
    PatentRoute,
    api_error,
    unavailable,
)
from services.api.reports import pdf_attachment, render_saved_report
from services.api.search_runs import Owner

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/v1/search-runs/{run_id}/reports",
    tags=["research"],
    route_class=PatentRoute,
    responses={
        status: {"model": PatentErrorEnvelope} for status in (401, 404, 409, 503)
    },
)
STATUS_COLUMNS = "g.id, g.run_id, g.status, g.created_at, g.started_at, g.finished_at"
VISIBLE_REPORT = """
    FROM generated_reports g JOIN search_runs r ON r.id = g.run_id
    WHERE g.id = %s AND g.run_id = %s AND r.user_id = %s
      AND (g.finished_at IS NULL OR g.finished_at >= now() - interval '1 hour')
"""
MAX_PDF_BYTES = 8 * 1024 * 1024


class ReportJob(BaseModel):
    id: UUID
    run_id: UUID
    status: Literal["queued", "running", "succeeded", "failed"]
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


def missing_report():
    return api_error(404, "REPORT_NOT_FOUND", "找不到此報告，或報告已過期。")


@router.post("", response_model=ReportJob, status_code=202)
def enqueue(run_id: UUID, account: Owner, response: Response):
    try:
        with engine.begin() as conn:
            owned = conn.exec_driver_sql(
                "SELECT id FROM search_runs WHERE id = %s AND user_id = %s FOR KEY SHARE",
                (run_id, account.id),
            ).scalar_one_or_none()
            if owned is None:
                return api_error(404, "RUN_NOT_FOUND", "找不到此搜尋紀錄。")
            row = (
                conn.exec_driver_sql(
                    f"""INSERT INTO generated_reports AS g (run_id) VALUES (%s)
                    ON CONFLICT DO NOTHING RETURNING {STATUS_COLUMNS}""",
                    (run_id,),
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                row = (
                    conn.exec_driver_sql(
                        f"""SELECT {STATUS_COLUMNS} FROM generated_reports g
                        WHERE g.run_id = %s
                        ORDER BY g.created_at DESC, g.id LIMIT 1""",
                        (run_id,),
                    )
                    .mappings()
                    .one_or_none()
                )
    except SQLAlchemyError:
        return unavailable()
    if row is None:
        return unavailable()
    response.headers["Location"] = f"/api/v1/search-runs/{run_id}/reports/{row['id']}"
    response.headers["Cache-Control"] = "private, no-store"
    return ReportJob.model_validate(row)


@router.get("/{report_id}", response_model=ReportJob)
def report_status(run_id: UUID, report_id: UUID, account: Owner, response: Response):
    try:
        with engine.connect() as conn:
            row = (
                conn.exec_driver_sql(
                    f"SELECT {STATUS_COLUMNS} {VISIBLE_REPORT}",
                    (report_id, run_id, account.id),
                )
                .mappings()
                .one_or_none()
            )
    except SQLAlchemyError:
        return unavailable()
    if row is None:
        return missing_report()
    response.headers["Cache-Control"] = "private, no-store"
    return ReportJob.model_validate(row)


@router.get(
    "/{report_id}/pdf",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
def download(run_id: UUID, report_id: UUID, account: Owner):
    try:
        with engine.connect() as conn:
            row = conn.exec_driver_sql(
                f"SELECT g.status, g.pdf {VISIBLE_REPORT}",
                (report_id, run_id, account.id),
            ).one_or_none()
    except SQLAlchemyError:
        return unavailable()
    if row is None:
        return missing_report()
    if row.status != "succeeded":
        return api_error(409, "REPORT_NOT_READY", "此報告尚未完成，或產生失敗。")
    return pdf_attachment(run_id, row.pdf)


def process_one_report() -> bool:
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """UPDATE generated_reports SET status = 'failed', finished_at = now()
               WHERE (status = 'running' AND started_at < now() - interval '6 minutes')
                  OR (status = 'queued' AND created_at < now() - interval '10 minutes')"""
        )
        conn.exec_driver_sql(
            "DELETE FROM generated_reports WHERE finished_at < now() - interval '1 hour'"
        )
        job = conn.exec_driver_sql(
            """UPDATE generated_reports g SET status = 'running', started_at = now()
               FROM search_runs r
               WHERE g.id = (SELECT id FROM generated_reports WHERE status = 'queued'
                             ORDER BY created_at, id LIMIT 1 FOR UPDATE SKIP LOCKED)
                 AND r.id = g.run_id
               RETURNING g.id, g.run_id, r.user_id"""
        ).one_or_none()
    if job is None:
        return False
    pdf = None
    try:
        rendered = render_saved_report(job.run_id, job.user_id)
        if (
            isinstance(rendered, bytes)
            and rendered.startswith(b"%PDF-")
            and len(rendered) <= MAX_PDF_BYTES
        ):
            pdf = rendered
    except Exception as error:
        logger.error(
            "PDF report failed report_id=%s type=%s", job.id, type(error).__name__
        )
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """UPDATE generated_reports SET status = %s, pdf = %s, finished_at = now()
               WHERE id = %s AND status = 'running'""",
            ("succeeded" if pdf else "failed", pdf, job.id),
        )
    return True
