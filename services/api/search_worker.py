"""Process queued searches outside the request/response lifecycle."""

import json
import logging
import signal
from collections.abc import Callable
from time import sleep

from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from services.api.db import engine
from services.api.model_limits import ModelBusy
from services.api.patents import HybridSearchRequest, run_hybrid
from services.api.report_jobs import process_one_report
from services.api.search_runs import persist_search

logger = logging.getLogger(__name__)


def process_one() -> bool:
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """UPDATE search_jobs SET status = 'failed', request = NULL,
                      error_code = 'SEARCH_JOB_EXPIRED', finished_at = now()
               WHERE (status = 'running' AND started_at < now() - interval '6 minutes')
                  OR (status = 'queued' AND created_at < now() - interval '10 minutes')"""
        )
        conn.exec_driver_sql(
            "DELETE FROM search_jobs WHERE finished_at < now() - interval '1 day'"
        )
        job = conn.exec_driver_sql(
            """UPDATE search_jobs j SET status = 'running', started_at = now()
               WHERE j.id = (SELECT id FROM search_jobs WHERE status = 'queued'
                             ORDER BY created_at, id LIMIT 1 FOR UPDATE SKIP LOCKED)
               RETURNING j.id, j.user_id, j.request"""
        ).one_or_none()
    if job is None:
        return False
    try:
        request = HybridSearchRequest.model_validate(job.request)
        result = run_hybrid(request, full_snapshot=True)
        error = (
            json.loads(result.body)["error"]["code"]
            if isinstance(result, JSONResponse)
            else None
        )
    except ModelBusy:
        error = "MODEL_BUSY"
    except Exception as exc:
        logger.error("Search job failed job_id=%s type=%s", job.id, type(exc).__name__)
        error = "SEARCH_JOB_FAILED"

    with engine.begin() as conn:
        owner = conn.exec_driver_sql(
            "SELECT id FROM users WHERE id = %s FOR KEY SHARE", (job.user_id,)
        ).scalar_one_or_none()
        if owner is None:
            return True
        active = conn.exec_driver_sql(
            "SELECT id FROM search_jobs WHERE id = %s AND status = 'running' FOR UPDATE",
            (job.id,),
        ).scalar_one_or_none()
        if active is None:
            return True
        if error:
            conn.exec_driver_sql(
                """UPDATE search_jobs SET status = 'failed', request = NULL,
                          finished_at = now(), error_code = %s WHERE id = %s""",
                (error, job.id),
            )
        else:
            saved = persist_search(conn, job.user_id, request, result)
            conn.exec_driver_sql(
                """UPDATE search_jobs SET status = 'succeeded', request = NULL,
                          finished_at = now(), run_id = %s WHERE id = %s""",
                (saved.id, job.id),
            )
    return True


def run_worker(should_stop: Callable[[], bool]) -> None:
    while not should_stop():
        try:
            searched = process_one()
            if should_stop():
                return
            reported = process_one_report()
            if searched or reported:
                continue
        except SQLAlchemyError as exc:
            logger.warning("Search worker database error type=%s", type(exc).__name__)
        if not should_stop():
            sleep(2)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    stopping = False

    def request_shutdown(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)
    run_worker(lambda: stopping)


if __name__ == "__main__":
    main()
