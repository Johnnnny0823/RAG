"""Collect one account's persisted research in a consistent read snapshot."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from services.api.db import engine

EXPORT_QUERIES = {
    "projects": """
        SELECT id, name, description, created_at FROM projects
        WHERE owner_user_id = %s ORDER BY created_at, id
    """,
    "saved_patents": """
        SELECT b.project_id, b.document_id, d.publication_no, d.document_stage,
               b.note, b.created_at
        FROM saved_patents b JOIN projects p ON p.id = b.project_id
        JOIN patent_documents d ON d.id = b.document_id
        WHERE p.owner_user_id = %s ORDER BY b.project_id, b.created_at, b.document_id
    """,
    "search_runs": """
        SELECT id, project_id, request, settings, created_at FROM search_runs
        WHERE user_id = %s ORDER BY created_at, id
    """,
    "search_candidates": """
        SELECT c.run_id, c.position, c.document_id, c.result
        FROM search_run_candidates c JOIN search_runs r ON r.id = c.run_id
        WHERE r.user_id = %s ORDER BY r.created_at, r.id, c.position
    """,
    "comparisons": """
        SELECT c.run_id, c.document_id, c.result
        FROM search_run_comparisons c JOIN search_runs r ON r.id = c.run_id
        WHERE r.user_id = %s ORDER BY r.created_at, r.id, c.document_id
    """,
    "sessions": """
        SELECT s.id, s.project_id, s.title, s.created_at
        FROM sessions s JOIN projects p ON p.id = s.project_id
        WHERE p.owner_user_id = %s ORDER BY s.created_at, s.id
    """,
    "messages": """
        SELECT m.id, m.session_id, m.sequence, m.role, m.content, m.created_at
        FROM messages m JOIN sessions s ON s.id = m.session_id
        JOIN projects p ON p.id = s.project_id
        WHERE p.owner_user_id = %s ORDER BY m.session_id, m.sequence
    """,
}


class ExportedAccount(BaseModel):
    id: UUID
    email: str
    created_at: datetime


class ResearchExport(BaseModel):
    format_version: Literal[1] = 1
    exported_at: datetime
    account: ExportedAccount
    projects: list[dict]
    saved_patents: list[dict]
    search_runs: list[dict]
    search_candidates: list[dict]
    comparisons: list[dict]
    sessions: list[dict]
    messages: list[dict]


def export_research(user_id: UUID) -> ResearchExport | None:
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn:
        account = (
            conn.exec_driver_sql(
                "SELECT id, email, created_at FROM users WHERE id = %s", (user_id,)
            )
            .mappings()
            .one_or_none()
        )
        if account is None:
            return None
        records = {
            key: [dict(row) for row in conn.exec_driver_sql(sql, (user_id,)).mappings()]
            for key, sql in EXPORT_QUERIES.items()
        }
        return ResearchExport(
            exported_at=datetime.now(UTC),
            account=ExportedAccount.model_validate(account),
            **records,
        )
