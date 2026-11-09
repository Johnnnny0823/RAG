"""Explicitly saved searches and their immutable candidate order."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import JSONResponse
from psycopg.types.json import Jsonb
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from services.api.db import engine
from services.api.comparisons import CompareRequest, ComparisonResponse, compare
from services.api.identity import Account, require_account
from services.api.patents import (
    HybridPatentHit,
    HybridSearchRequest,
    PatentErrorEnvelope,
    PatentRoute,
    api_error,
    run_hybrid,
    unavailable,
)

router = APIRouter(
    prefix="/api/v1/search-runs",
    tags=["research"],
    route_class=PatentRoute,
    responses={code: {"model": PatentErrorEnvelope} for code in (401, 404, 422, 503)},
)
Owner = Annotated[Account, Depends(require_account)]


class SavedRun(BaseModel):
    id: UUID
    created_at: datetime


class RunDetails(SavedRun):
    request: HybridSearchRequest
    settings: dict
    items: list[HybridPatentHit]
    comparisons: list[ComparisonResponse]


@router.post("", response_model=SavedRun, status_code=201)
def save_search(request: HybridSearchRequest, account: Owner, response: Response):
    result = run_hybrid(request, full_snapshot=True)
    if isinstance(result, JSONResponse):
        return result
    settings = result.model_dump(
        mode="json", exclude={"items", "limit", "offset", "has_more"}
    )
    try:
        with engine.begin() as conn:
            run = (
                conn.exec_driver_sql(
                    """INSERT INTO search_runs (user_id,request,settings) VALUES (%s,%s,%s)
                   RETURNING id, created_at""",
                    (
                        account.id,
                        Jsonb(request.model_dump(mode="json")),
                        Jsonb(settings),
                    ),
                )
                .mappings()
                .one()
            )
            if result.items:
                conn.exec_driver_sql(
                    """INSERT INTO search_run_candidates (run_id, position, document_id, result)
                       VALUES (%s,%s,%s,%s)""",
                    [
                        (
                            run["id"],
                            position,
                            hit.document_id,
                            Jsonb(hit.model_dump(mode="json")),
                        )
                        for position, hit in enumerate(result.items, 1)
                    ],
                )
    except SQLAlchemyError:
        return unavailable()
    response.headers["Cache-Control"] = "no-store"
    return SavedRun.model_validate(run)


@router.get("", response_model=list[SavedRun])
def list_searches(
    account: Owner,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
):
    try:
        with engine.connect() as conn:
            rows = (
                conn.exec_driver_sql(
                    """SELECT id, created_at FROM search_runs WHERE user_id=%s
                   ORDER BY created_at DESC, id LIMIT %s OFFSET %s""",
                    (account.id, limit, offset),
                )
                .mappings()
                .all()
            )
    except SQLAlchemyError:
        return unavailable()
    response.headers["Cache-Control"] = "no-store"
    return [SavedRun.model_validate(row) for row in rows]


@router.get("/{run_id}", response_model=RunDetails)
def load_search(run_id: UUID, account: Owner, response: Response):
    try:
        with engine.connect() as conn:
            run = (
                conn.exec_driver_sql(
                    "SELECT id, created_at, request, settings FROM search_runs WHERE id=%s AND user_id=%s",
                    (run_id, account.id),
                )
                .mappings()
                .one_or_none()
            )
            if run is None:
                return api_error(404, "RUN_NOT_FOUND", "找不到此搜尋紀錄。")
            results = (
                conn.exec_driver_sql(
                    """SELECT c.result FROM search_run_candidates c JOIN search_runs r ON r.id=c.run_id
                   WHERE r.id=%s AND r.user_id=%s ORDER BY c.position""",
                    (run_id, account.id),
                )
                .scalars()
                .all()
            )
    except SQLAlchemyError:
        return unavailable()
    response.headers["Cache-Control"] = "no-store"
    try:
        with engine.connect() as conn:
            comparisons = (
                conn.exec_driver_sql(
                    """SELECT c.result FROM search_run_comparisons c JOIN search_runs r ON r.id=c.run_id
                   WHERE r.id=%s AND r.user_id=%s ORDER BY c.document_id""",
                    (run_id, account.id),
                )
                .scalars()
                .all()
            )
    except SQLAlchemyError:
        return unavailable()
    return RunDetails.model_validate(
        {**run, "items": results, "comparisons": comparisons}
    )


@router.post("/{run_id}/comparisons/{document_id}", response_model=ComparisonResponse)
def save_comparison(
    run_id: UUID, document_id: UUID, account: Owner, response: Response
):
    try:
        with engine.connect() as conn:
            row = conn.exec_driver_sql(
                """SELECT r.request, comparison.result
                   FROM search_runs r
                   JOIN search_run_candidates c ON c.run_id=r.id
                   LEFT JOIN search_run_comparisons comparison
                     ON comparison.run_id=r.id AND comparison.document_id=c.document_id
                   WHERE r.id=%s AND r.user_id=%s AND c.document_id=%s""",
                (run_id, account.id, document_id),
            ).one_or_none()
        if row is None:
            return api_error(404, "RUN_NOT_FOUND", "找不到此搜尋紀錄或候選文件。")
        response.headers["Cache-Control"] = "no-store"
        if row.result is not None:
            return ComparisonResponse.model_validate(row.result)
        request = HybridSearchRequest.model_validate(row.request)
        if not request.features:
            return api_error(422, "INVALID_REQUEST", "請先保存包含技術特徵的搜尋。")
        result = compare(document_id, CompareRequest(features=request.features))
        if isinstance(result, JSONResponse):
            return result
        with engine.begin() as conn:
            conn.exec_driver_sql(
                """INSERT INTO search_run_comparisons (run_id, document_id, result)
                   SELECT id, %s, %s FROM search_runs WHERE id=%s AND user_id=%s
                   ON CONFLICT DO NOTHING""",
                (
                    document_id,
                    Jsonb(result.model_dump(mode="json")),
                    run_id,
                    account.id,
                ),
            )
            saved = conn.exec_driver_sql(
                """SELECT c.result FROM search_run_comparisons c JOIN search_runs r ON r.id=c.run_id
                   WHERE r.id=%s AND r.user_id=%s AND c.document_id=%s""",
                (run_id, account.id, document_id),
            ).scalar_one_or_none()
    except SQLAlchemyError:
        return unavailable()
    if saved is None:
        return api_error(404, "RUN_NOT_FOUND", "找不到此搜尋紀錄或候選文件。")
    return ComparisonResponse.model_validate(saved)
