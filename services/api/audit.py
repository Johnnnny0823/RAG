"""Privacy-safe operational audit log writer and owner-scoped reader."""

from datetime import datetime
import logging
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from services.api.db import engine
from services.api.identity import Account, require_account
from services.api.patents import PatentErrorEnvelope, PatentRoute, unavailable

logger = logging.getLogger(__name__)
Outcome = Literal["success", "denied", "failed"]

router = APIRouter(
    prefix="/api/v1/audit-logs",
    tags=["audit"],
    route_class=PatentRoute,
    responses={code: {"model": PatentErrorEnvelope} for code in (401, 422, 503)},
)


class AuditLogEntry(BaseModel):
    id: int
    action: str
    resource_type: str
    resource_id: str | None
    outcome: Outcome
    created_at: datetime


class AuditLogPage(BaseModel):
    items: list[AuditLogEntry]
    limit: int
    offset: int
    has_more: bool


def record_audit_event(
    action: str,
    resource_type: str,
    *,
    user_id: UUID,
    resource_id: str | UUID | None = None,
    outcome: Outcome = "success",
) -> None:
    """Best-effort insert of an audit event without leaking secrets or query text."""
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql(
                """INSERT INTO audit_logs (user_id, action, resource_type, resource_id, outcome)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    user_id,
                    action,
                    resource_type,
                    str(resource_id) if resource_id is not None else None,
                    outcome,
                ),
            )
    except SQLAlchemyError as exc:
        logger.warning(
            "Audit event skipped action=%s type=%s", action, type(exc).__name__
        )


def fetch_owner_audit_logs(
    user_id: UUID, limit: int, offset: int
) -> tuple[list[AuditLogEntry], bool]:
    with engine.connect() as conn:
        rows = (
            conn.exec_driver_sql(
                """SELECT id, action, resource_type, resource_id, outcome, created_at
                   FROM audit_logs
                   WHERE user_id = %s
                   ORDER BY created_at DESC, id DESC
                   LIMIT %s OFFSET %s""",
                (user_id, limit + 1, offset),
            )
            .mappings()
            .all()
        )
    has_more = len(rows) > limit
    return [AuditLogEntry.model_validate(row) for row in rows[:limit]], has_more


@router.get("", response_model=AuditLogPage)
def list_audit_logs(
    account: Annotated[Account, Depends(require_account)],
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
):
    try:
        items, has_more = fetch_owner_audit_logs(account.id, limit, offset)
    except SQLAlchemyError:
        return unavailable()
    response.headers["Cache-Control"] = "no-store"
    return AuditLogPage(items=items, limit=limit, offset=offset, has_more=has_more)
