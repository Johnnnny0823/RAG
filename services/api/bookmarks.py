"""Private project bookmarks for official patent document versions."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from services.api.db import engine
from services.api.patents import (
    DOCUMENTS_FROM,
    PUBLIC_DOCUMENTS,
    PUBLIC_DOCUMENT_FILTER,
    SUMMARY_FIELDS,
    PatentErrorEnvelope,
    PatentRoute,
    PatentVersion,
    api_error,
    unavailable,
)
from services.api.projects import Owner, project_missing

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/patents",
    tags=["research"],
    route_class=PatentRoute,
    responses={code: {"model": PatentErrorEnvelope} for code in (401, 404, 422, 503)},
)


class NoteInput(BaseModel):
    note: str = Field(max_length=4000)


class Bookmark(PatentVersion):
    note: str
    created_at: datetime


class BookmarkStatus(BaseModel):
    document_id: UUID


def owned_project(conn, project_id, owner_id):
    return (
        conn.exec_driver_sql(
            "SELECT id FROM projects WHERE id=%s AND owner_user_id=%s",
            (project_id, owner_id),
        ).scalar_one_or_none()
        is not None
    )


@router.get("", response_model=list[Bookmark])
def list_bookmarks(
    project_id: UUID,
    account: Owner,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
):
    try:
        with engine.connect() as conn:
            if not owned_project(conn, project_id, account.id):
                return project_missing()
            rows = (
                conn.exec_driver_sql(
                    f"""SELECT {SUMMARY_FIELDS}, b.note, b.created_at
                    {DOCUMENTS_FROM}
                    JOIN saved_patents b ON b.document_id=d.id
                    JOIN projects p ON p.id=b.project_id
                    {PUBLIC_DOCUMENT_FILTER} AND p.id=%s AND p.owner_user_id=%s
                    ORDER BY b.created_at DESC, b.document_id LIMIT %s OFFSET %s""",
                    (project_id, account.id, limit, offset),
                )
                .mappings()
                .all()
            )
    except SQLAlchemyError:
        return unavailable()
    response.headers["Cache-Control"] = "no-store"
    return [Bookmark.model_validate(row) for row in rows]


@router.put("/{document_id}", response_model=BookmarkStatus)
def add_bookmark(
    project_id: UUID, document_id: UUID, account: Owner, response: Response
):
    try:
        with engine.begin() as conn:
            if not owned_project(conn, project_id, account.id):
                return project_missing()
            exists = conn.exec_driver_sql(
                f"""WITH eligible AS (SELECT d.id {PUBLIC_DOCUMENTS} AND d.id=%s),
                    added AS (
                        INSERT INTO saved_patents (project_id, document_id)
                        SELECT p.id, eligible.id FROM projects p CROSS JOIN eligible
                        WHERE p.id=%s AND p.owner_user_id=%s
                        ON CONFLICT DO NOTHING
                    )
                    SELECT id FROM eligible""",
                (document_id, project_id, account.id),
            ).scalar_one_or_none()
    except SQLAlchemyError:
        return unavailable()
    if exists is None:
        return api_error(404, "PATENT_NOT_FOUND", "找不到此專利文件版本。")
    response.headers["Cache-Control"] = "no-store"
    return BookmarkStatus(document_id=document_id)


@router.patch("/{document_id}", response_model=NoteInput)
def update_note(
    project_id: UUID,
    document_id: UUID,
    payload: NoteInput,
    account: Owner,
    response: Response,
):
    try:
        with engine.begin() as conn:
            note = conn.exec_driver_sql(
                """UPDATE saved_patents b SET note=%s FROM projects p
                   WHERE p.id=b.project_id AND p.id=%s AND p.owner_user_id=%s AND b.document_id=%s
                   RETURNING b.note""",
                (payload.note, project_id, account.id, document_id),
            ).scalar_one_or_none()
    except SQLAlchemyError:
        return unavailable()
    if note is None:
        return api_error(404, "BOOKMARK_NOT_FOUND", "找不到此收藏。")
    response.headers["Cache-Control"] = "no-store"
    return NoteInput(note=note)


@router.delete("/{document_id}", response_model=BookmarkStatus)
def remove_bookmark(
    project_id: UUID, document_id: UUID, account: Owner, response: Response
):
    try:
        with engine.begin() as conn:
            removed = conn.exec_driver_sql(
                """DELETE FROM saved_patents b USING projects p
                   WHERE p.id=b.project_id AND p.id=%s AND p.owner_user_id=%s AND b.document_id=%s
                   RETURNING b.document_id""",
                (project_id, account.id, document_id),
            ).scalar_one_or_none()
    except SQLAlchemyError:
        return unavailable()
    if removed is None:
        return api_error(404, "BOOKMARK_NOT_FOUND", "找不到此收藏。")
    response.headers["Cache-Control"] = "no-store"
    return BookmarkStatus(document_id=document_id)
