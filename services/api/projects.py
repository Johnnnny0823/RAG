"""Owner-scoped research project metadata."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, StringConstraints
from sqlalchemy.exc import SQLAlchemyError

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


class ProjectInput(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
    ]
    description: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=2000)
    ] = ""


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
