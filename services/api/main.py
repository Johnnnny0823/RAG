import logging
from typing import Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from services.api.db import check_database
from services.api.comparisons import router as comparisons_router
from services.api.accounts import router as accounts_router
from services.api.search_runs import router as search_runs_router
from services.api.patents import router as patents_router
from services.api.projects import router as projects_router
from services.api.bookmarks import router as bookmarks_router
from services.api.sessions import router as sessions_router
from services.api.queries import router as queries_router

logger = logging.getLogger(__name__)
app = FastAPI(title="PatentScope AI", version="0.1.0")
app.include_router(patents_router)
app.include_router(queries_router)
app.include_router(comparisons_router)
app.include_router(accounts_router)
app.include_router(search_runs_router)
app.include_router(projects_router)
app.include_router(bookmarks_router)
app.include_router(sessions_router)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadyResponse(BaseModel):
    status: Literal["ready"] = "ready"


class ReadinessError(BaseModel):
    code: Literal["DATABASE_UNAVAILABLE"] = "DATABASE_UNAVAILABLE"
    message: str = "資料庫或向量擴充功能目前無法使用。"
    request_id: UUID


class ErrorResponse(BaseModel):
    error: ReadinessError


@app.get("/api/v1/health")
def health() -> HealthResponse:
    return HealthResponse()


@app.get(
    "/api/v1/ready",
    response_model=ReadyResponse,
    responses={503: {"model": ErrorResponse}},
)
def ready(response: Response) -> ReadyResponse | JSONResponse:
    try:
        check_database()
    except SQLAlchemyError as exc:
        error = ReadinessError(request_id=uuid4())
        logger.warning(
            "Database readiness failed request_id=%s type=%s",
            error.request_id,
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(error=error).model_dump(mode="json"),
            headers={"Cache-Control": "no-store"},
        )
    response.headers["Cache-Control"] = "no-store"
    return ReadyResponse()
