"""Owner-scoped research sessions with typed local AI analysis turns."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Response
from fastapi.responses import JSONResponse
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy.exc import SQLAlchemyError

from services.api.db import engine
from services.api.patents import (
    PatentErrorEnvelope,
    PatentRoute,
    api_error,
    unavailable,
)
from services.api.projects import Owner, project_missing
from services.api.queries import AnalyzeRequest, AnalyzeResponse, analyze

router = APIRouter(
    prefix="/api/v1/sessions",
    tags=["research"],
    route_class=PatentRoute,
    responses={code: {"model": PatentErrorEnvelope} for code in (401, 404, 422, 503)},
)


class SessionInput(BaseModel):
    project_id: UUID
    title: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
    ]


class Session(SessionInput):
    id: UUID
    created_at: datetime


class MessageFields(BaseModel):
    id: UUID
    created_at: datetime


class UserMessage(MessageFields):
    role: Literal["user"]
    content: str


class AssistantMessage(MessageFields):
    role: Literal["assistant"]
    content: AnalyzeResponse


Message = Annotated[UserMessage | AssistantMessage, Field(discriminator="role")]
SESSION_OWNER = """
    FROM sessions s JOIN projects p ON p.id=s.project_id
    WHERE s.id=%s AND p.owner_user_id=%s
"""


def session_missing():
    return api_error(404, "SESSION_NOT_FOUND", "找不到此 AI Session。")


@router.post("", response_model=Session, status_code=201)
def create_session(payload: SessionInput, account: Owner, response: Response):
    try:
        with engine.begin() as conn:
            row = (
                conn.exec_driver_sql(
                    """INSERT INTO sessions (project_id, title)
                   SELECT id, %s FROM projects WHERE id=%s AND owner_user_id=%s
                   RETURNING id, project_id, title, created_at""",
                    (payload.title, payload.project_id, account.id),
                )
                .mappings()
                .one_or_none()
            )
    except SQLAlchemyError:
        return unavailable()
    if row is None:
        return project_missing()
    response.headers["Cache-Control"] = "no-store"
    return Session.model_validate(row)


@router.get("", response_model=list[Session])
def list_sessions(
    project_id: UUID,
    account: Owner,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
):
    try:
        with engine.connect() as conn:
            project = conn.exec_driver_sql(
                "SELECT id FROM projects WHERE id=%s AND owner_user_id=%s",
                (project_id, account.id),
            ).scalar_one_or_none()
            if project is None:
                return project_missing()
            rows = (
                conn.exec_driver_sql(
                    """SELECT s.id, s.project_id, s.title, s.created_at
                   FROM sessions s JOIN projects p ON p.id=s.project_id
                   WHERE p.id=%s AND p.owner_user_id=%s
                   ORDER BY s.created_at DESC, s.id LIMIT %s OFFSET %s""",
                    (project_id, account.id, limit, offset),
                )
                .mappings()
                .all()
            )
    except SQLAlchemyError:
        return unavailable()
    response.headers["Cache-Control"] = "no-store"
    return rows


@router.get("/{session_id}/messages", response_model=list[Message])
def list_messages(
    session_id: UUID,
    account: Owner,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 40,
    before: Annotated[UUID | None, Query()] = None,
):
    try:
        with engine.connect() as conn:
            owner = conn.exec_driver_sql(
                f"SELECT s.id {SESSION_OWNER}", (session_id, account.id)
            ).scalar_one_or_none()
            if owner is None:
                return session_missing()
            rows = (
                conn.exec_driver_sql(
                    f"""SELECT id, role, content, created_at FROM (
                        SELECT m.id, m.role, m.content, m.created_at, m.sequence
                        FROM messages m WHERE m.session_id=(SELECT s.id {SESSION_OWNER})
                        AND (%s::uuid IS NULL OR m.sequence < (
                            SELECT sequence FROM messages WHERE session_id=m.session_id AND id=%s
                        ))
                        ORDER BY m.sequence DESC LIMIT %s
                    ) AS recent ORDER BY sequence""",
                    (session_id, account.id, before, before, limit),
                )
                .mappings()
                .all()
            )
    except SQLAlchemyError:
        return unavailable()
    response.headers["Cache-Control"] = "no-store"
    return rows


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: UUID, account: Owner):
    try:
        with engine.begin() as conn:
            removed = conn.exec_driver_sql(
                """DELETE FROM sessions s USING projects p
                   WHERE s.project_id=p.id AND s.id=%s AND p.owner_user_id=%s
                   RETURNING s.id""",
                (session_id, account.id),
            ).scalar_one_or_none()
    except SQLAlchemyError:
        return unavailable()
    if removed is None:
        return session_missing()
    return Response(status_code=204, headers={"Cache-Control": "no-store"})


@router.post(
    "/{session_id}/messages",
    response_model=list[Message],
    status_code=201,
    responses={429: {"model": PatentErrorEnvelope}},
)
def add_turn(
    session_id: UUID, payload: AnalyzeRequest, account: Owner, response: Response
):
    try:
        with engine.connect() as conn:
            owner = conn.exec_driver_sql(
                f"SELECT s.id {SESSION_OWNER}", (session_id, account.id)
            ).scalar_one_or_none()
        if owner is None:
            return session_missing()
        result = analyze(payload)
        if isinstance(result, JSONResponse):
            return result
        with engine.begin() as conn:
            owner = conn.exec_driver_sql(
                f"SELECT s.id {SESSION_OWNER} FOR UPDATE OF s", (session_id, account.id)
            ).scalar_one_or_none()
            if owner is None:
                return session_missing()
            rows = (
                conn.exec_driver_sql(
                    """WITH saved AS (
                       INSERT INTO messages (session_id, role, content)
                       VALUES (%s, 'user', %s), (%s, 'assistant', %s)
                       RETURNING id, role, content, created_at, sequence
                   ) SELECT id, role, content, created_at FROM saved ORDER BY sequence""",
                    (
                        session_id,
                        Jsonb(payload.query),
                        session_id,
                        Jsonb(result.model_dump(mode="json")),
                    ),
                )
                .mappings()
                .all()
            )
    except SQLAlchemyError:
        return unavailable()
    response.headers["Cache-Control"] = "no-store"
    return rows
