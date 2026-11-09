"""Owner-scoped research project metadata."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, StringConstraints
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from services.api.db import engine
from services.api.identity import Account, require_account
from services.api.patents import (
    PatentErrorEnvelope,
    PatentRoute,
    api_error,
    unavailable,
)

router = APIRouter(
    prefix="/api/v1/projects",
    tags=["research"],
    route_class=PatentRoute,
    responses={code: {"model": PatentErrorEnvelope} for code in (401, 404, 422, 503)},
)
Owner = Annotated[Account, Depends(require_account)]
ProjectName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
]
ProjectDescription = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=2000)
]


class ProjectInput(BaseModel):
    name: ProjectName
    description: ProjectDescription = ""


class ProjectPatch(BaseModel):
    name: ProjectName | None = None
    description: ProjectDescription | None = None


class Project(ProjectInput):
    id: UUID
    created_at: datetime


def project_missing():
    return api_error(404, "PROJECT_NOT_FOUND", "找不到此研究專案。")


@router.post("", response_model=Project, status_code=201)
def create_project(payload: ProjectInput, account: Owner, response: Response):
    try:
        with engine.begin() as conn:
            row = (
                conn.exec_driver_sql(
                    """INSERT INTO projects (owner_user_id, name, description)
                   VALUES (%s, %s, %s) RETURNING id, name, description, created_at""",
                    (account.id, payload.name, payload.description),
                )
                .mappings()
                .one()
            )
    except SQLAlchemyError:
        return unavailable()
    response.headers["Cache-Control"] = "no-store"
    return Project.model_validate(row)


@router.get("", response_model=list[Project])
def list_projects(
    account: Owner,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
):
    try:
        with engine.connect() as conn:
            rows = (
                conn.exec_driver_sql(
                    """SELECT id, name, description, created_at FROM projects
                   WHERE owner_user_id=%s ORDER BY created_at DESC, id LIMIT %s OFFSET %s""",
                    (account.id, limit, offset),
                )
                .mappings()
                .all()
            )
    except SQLAlchemyError:
        return unavailable()
    response.headers["Cache-Control"] = "no-store"
    return [Project.model_validate(row) for row in rows]


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: UUID, account: Owner, response: Response):
    try:
        with engine.connect() as conn:
            row = (
                conn.exec_driver_sql(
                    """SELECT id, name, description, created_at FROM projects
                   WHERE id=%s AND owner_user_id=%s""",
                    (project_id, account.id),
                )
                .mappings()
                .one_or_none()
            )
    except SQLAlchemyError:
        return unavailable()
    if row is None:
        return project_missing()
    response.headers["Cache-Control"] = "no-store"
    return Project.model_validate(row)


@router.patch("/{project_id}", response_model=Project)
def update_project(
    project_id: UUID, payload: ProjectPatch, account: Owner, response: Response
):
    try:
        with engine.begin() as conn:
            row = (
                conn.exec_driver_sql(
                    """UPDATE projects SET name=COALESCE(%s, name), description=COALESCE(%s, description)
                   WHERE id=%s AND owner_user_id=%s RETURNING id, name, description, created_at""",
                    (payload.name, payload.description, project_id, account.id),
                )
                .mappings()
                .one_or_none()
            )
    except SQLAlchemyError:
        return unavailable()
    if row is None:
        return project_missing()
    response.headers["Cache-Control"] = "no-store"
    return Project.model_validate(row)


@router.delete(
    "/{project_id}", status_code=204, responses={409: {"model": PatentErrorEnvelope}}
)
def delete_project(project_id: UUID, account: Owner):
    try:
        with engine.begin() as conn:
            removed = conn.exec_driver_sql(
                "DELETE FROM projects WHERE id=%s AND owner_user_id=%s RETURNING id",
                (project_id, account.id),
            ).scalar_one_or_none()
    except IntegrityError as error:
        if getattr(error.orig, "sqlstate", None) == "23503":
            return api_error(
                409,
                "PROJECT_NOT_EMPTY",
                "專案仍有搜尋紀錄、收藏或 AI Session，無法刪除。",
            )
        return unavailable()
    except SQLAlchemyError:
        return unavailable()
    if removed is None:
        return project_missing()
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
