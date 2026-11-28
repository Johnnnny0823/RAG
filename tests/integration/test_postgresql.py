"""Exercise the migrated PostgreSQL schema and API with an isolated database."""

import hashlib
import os
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import psycopg
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from psycopg.errors import ForeignKeyViolation, InsufficientPrivilege
from psycopg.types.json import Jsonb
from sqlalchemy.exc import IntegrityError, ProgrammingError

from services.api.db import engine
from services.api.main import app
from services.api import report_jobs, search_worker
from services.api.patents import HybridSearchResults

pytestmark = pytest.mark.skipif(
    os.getenv("PATENTSCOPE_PG_INTEGRATION") != "1",
    reason="Requires the isolated PostgreSQL integration stack",
)


@pytest.fixture(autouse=True)
def require_test_database():
    assert os.environ["PGHOST"] == "127.0.0.1"
    assert os.environ["PGDATABASE"] == "patentscope_test"
    assert os.environ["PGPORT"].isdecimal()
    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT current_database()").scalar_one() == (
            "patentscope_test"
        )


def test_migration_head_and_vector_operator():
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "database/migrations"))
    expected = ScriptDirectory.from_config(config).get_current_head()
    with psycopg.connect(
        user=os.environ["PATENTSCOPE_PG_ADMIN_USER"],
        password=os.environ["PATENTSCOPE_PG_ADMIN_PASSWORD"],
    ) as admin:
        assert (
            admin.execute("SELECT version_num FROM alembic_version").fetchone()[0]
            == expected
        )
    with engine.connect() as conn:
        assert (
            conn.exec_driver_sql(
                "SELECT '[1, 2]'::vector <-> '[4, 6]'::vector"
            ).scalar_one()
            == 5
        )
    with TestClient(app) as client:
        assert client.get("/api/v1/ready").json() == {"status": "ready"}


def test_api_role_cannot_write_corpus_or_manage_schema():
    with engine.connect() as conn:
        role = conn.exec_driver_sql(
            """SELECT current_user, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls
               FROM pg_roles WHERE rolname = current_user"""
        ).one()
        assert tuple(role) == ("patentscope_api", False, False, False, False)
        conn.exec_driver_sql("SELECT id FROM patent_documents LIMIT 1").all()
        conn.exec_driver_sql("SELECT page_number FROM gazette_pdf_pages LIMIT 1").all()
        conn.exec_driver_sql("SELECT priority_no FROM patent_priorities LIMIT 1").all()
        for statement in (
            "DELETE FROM patent_documents WHERE false",
            "DELETE FROM gazette_pdf_pages WHERE false",
            "DELETE FROM patent_priorities WHERE false",
            "CREATE TABLE public.should_not_create (id integer)",
            "SELECT version_num FROM alembic_version",
        ):
            with pytest.raises(ProgrammingError) as error, conn.begin_nested():
                conn.exec_driver_sql(statement)
            assert isinstance(error.value.orig, InsufficientPrivilege)


@pytest.fixture
def accounts():
    with TestClient(app) as client:
        sessions = []
        try:
            for _ in range(2):
                credentials = {
                    "email": f"pg-test-{uuid4()}@example.invalid",
                    "password": str(uuid4()),
                }
                registration = client.post("/api/v1/auth/register", json=credentials)
                assert registration.status_code == 201
                login = client.post("/api/v1/auth/login", json=credentials)
                assert login.status_code == 200
                headers = {"Authorization": "Bearer " + login.json()["access_token"]}
                sessions.append((UUID(registration.json()["id"]), headers, credentials))
            yield client, sessions
        finally:
            for _, headers, credentials in sessions:
                response = client.request(
                    "DELETE",
                    "/api/v1/me",
                    headers=headers,
                    json={"password": credentials["password"]},
                )
                assert response.status_code == 204


def test_account_audit_and_corpus_routes_work_with_the_restricted_api_role(accounts):
    client, ((_, first, _), (_, second, _)) = accounts
    assert client.get("/api/v1/audit-logs").status_code == 401
    first_log = client.get("/api/v1/audit-logs", headers=first)
    second_log = client.get("/api/v1/audit-logs", headers=second)
    assert first_log.status_code == second_log.status_code == 200
    assert first_log.headers["cache-control"] == "no-store"
    assert (
        first_log.headers["permissions-policy"]
        == "camera=(), microphone=(), geolocation=()"
    )
    first_entries = first_log.json()["items"]
    second_entries = second_log.json()["items"]
    assert [entry["action"] for entry in first_entries] == ["register"]
    assert [entry["action"] for entry in second_entries] == ["register"]
    assert first_entries[0]["id"] != second_entries[0]["id"]
    assert first_entries[0]["resource_id"] is None
    corpus = client.get("/api/v1/corpus/status")
    assert corpus.status_code == 200
    assert corpus.json()["documents_total"] >= 0


def test_repeated_login_failures_are_throttled_per_address(accounts):
    client, ((_, _, target), (_, _, bystander)) = accounts
    guess = {"email": target["email"], "password": "wrong-password-guess"}
    for _ in range(5):
        assert client.post("/api/v1/auth/login", json=guess).status_code == 401

    for credentials in (guess, target):
        limited = client.post("/api/v1/auth/login", json=credentials)
        assert limited.status_code == 429
        assert limited.json()["error"]["code"] == "LOGIN_THROTTLED"
        assert 0 < int(limited.headers["Retry-After"]) <= 900
    assert client.post("/api/v1/auth/login", json=bystander).status_code == 200

    key = hashlib.sha256(target["email"].encode()).digest()
    with engine.begin() as conn:
        stored = conn.exec_driver_sql(
            "SELECT count(*) FROM login_failures WHERE email_hash = %s", (key,)
        ).scalar_one()
        assert stored == 5
    # Modify the synthetic timestamps as the test administrator.
    with psycopg.connect(
        user=os.environ["PATENTSCOPE_PG_ADMIN_USER"],
        password=os.environ["PATENTSCOPE_PG_ADMIN_PASSWORD"],
    ) as admin:
        admin.execute(
            """UPDATE login_failures SET failed_at = failed_at - interval '16 minutes'
               WHERE email_hash = %s""",
            (key,),
        )
    assert client.post("/api/v1/auth/login", json=target).status_code == 200
    with engine.connect() as conn:
        assert (
            conn.exec_driver_sql(
                "SELECT count(*) FROM login_failures WHERE email_hash = %s", (key,)
            ).scalar_one()
            == 0
        )


def test_projects_isolated_in_api_and_foreign_key(accounts):
    client, ((owner_id, owner, _), (other_id, other, _)) = accounts
    response = client.post("/api/v1/projects", headers=owner, json={"name": "PG test"})
    assert response.status_code == 201
    project_id = UUID(response.json()["id"])
    path = f"/api/v1/projects/{project_id}"

    assert client.get(path, headers=owner).json()["name"] == "PG test"
    denied = client.get(path, headers=other)
    assert denied.status_code == 404
    assert denied.json()["error"]["code"] == "PROJECT_NOT_FOUND"

    with engine.connect() as conn:
        assert (
            conn.exec_driver_sql(
                "SELECT owner_user_id FROM projects WHERE id = %s", (project_id,)
            ).scalar_one()
            == owner_id
        )
        with pytest.raises(IntegrityError) as error, conn.begin_nested():
            conn.exec_driver_sql(
                """INSERT INTO search_runs (user_id, project_id, request, settings)
                   VALUES (%s, %s, '{}'::jsonb, '{}'::jsonb)""",
                (other_id, project_id),
            )
        assert isinstance(error.value.orig, ForeignKeyViolation)
        assert error.value.orig.diag.constraint_name == "fk_search_runs_owner_project"


def test_private_research_export_has_only_the_authenticated_accounts_data(accounts):
    client, ((owner_id, owner, _), (other_id, other, _)) = accounts
    for user_id, headers, text in (
        (owner_id, owner, "owned synthetic content"),
        (other_id, other, "unrelated synthetic content"),
    ):
        project = client.post("/api/v1/projects", headers=headers, json={"name": text})
        assert project.status_code == 201
        project_id = UUID(project.json()["id"])
        session = client.post(
            "/api/v1/sessions",
            headers=headers,
            json={"project_id": str(project_id), "title": text},
        )
        assert session.status_code == 201
        with engine.begin() as conn:
            conn.exec_driver_sql(
                """INSERT INTO search_runs (user_id, project_id, request, settings)
                   VALUES (%s, %s, jsonb_build_object('query', %s::text), '{}'::jsonb)""",
                (user_id, project_id, text),
            )
            conn.exec_driver_sql(
                """INSERT INTO messages (session_id, role, content)
                   VALUES (%s, 'user', to_jsonb(%s::text))""",
                (UUID(session.json()["id"]), text),
            )

    assert client.get("/api/v1/me/export").status_code == 401
    response = client.get("/api/v1/me/export", headers=owner)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.headers["Content-Disposition"].startswith("attachment;")
    bundle = response.json()
    assert bundle["format_version"] == 1
    assert bundle["account"]["id"] == str(owner_id)
    assert set(bundle["account"]) == {"id", "email", "created_at"}
    assert [row["name"] for row in bundle["projects"]] == ["owned synthetic content"]
    assert [row["request"]["query"] for row in bundle["search_runs"]] == [
        "owned synthetic content"
    ]
    assert [row["title"] for row in bundle["sessions"]] == ["owned synthetic content"]
    assert [row["content"] for row in bundle["messages"]] == ["owned synthetic content"]
    assert str(other_id) not in response.text
    assert "unrelated synthetic content" not in response.text
    assert "password" not in response.text and "token_hash" not in response.text


def test_background_search_saves_snapshot_only_for_completed_owner_job(
    accounts, monkeypatch
):
    client, ((_, owner, _), (_, other, _)) = accounts
    outcomes = []
    monkeypatch.setattr(
        search_worker,
        "write_activity",
        lambda event, _, **info: outcomes.append((event, info)),
    )
    response = client.post("/api/v1/search-jobs", headers=owner, json={"query": "DEMO"})
    assert response.status_code == 202
    path = response.headers["Location"]
    assert response.json()["status"] == "queued"
    assert client.get(path, headers=other).status_code == 404
    assert client.post(f"{path}/cancel", headers=other).status_code == 404
    assert (
        client.post(
            "/api/v1/search-jobs", headers=owner, json={"query": "DEMO again"}
        ).status_code
        == 409
    )

    result = HybridSearchResults(
        items=[],
        tokenizer_version="DEMO",
        model_name="DEMO",
        model_digest="a" * 64,
        pipeline="DEMO",
        query_expansion_version="DEMO",
        rrf_k=60,
        candidate_limit=100,
        applied_feature_ids=[],
        reranker=None,
        limit=20,
        offset=0,
        has_more=False,
    )

    def run_hybrid(request, *, full_snapshot):
        assert full_snapshot and request.query == "DEMO"
        assert client.get(path, headers=owner).json()["status"] == "running"
        return result

    monkeypatch.setattr(search_worker, "run_hybrid", run_hybrid)
    assert search_worker.process_one()
    completed = client.get(path, headers=owner).json()
    assert completed["status"] == "succeeded"
    saved_path = f"/api/v1/search-runs/{completed['run_id']}"
    assert client.get(saved_path, headers=owner).json()["request"]["query"] == "DEMO"
    assert client.get(saved_path, headers=other).status_code == 404
    with engine.connect() as conn:
        assert conn.exec_driver_sql(
            "SELECT request IS NULL FROM search_jobs WHERE id=%s", (completed["id"],)
        ).scalar_one()

    queued = client.post(
        "/api/v1/search-jobs", headers=owner, json={"query": "DEMO cancel"}
    )
    path = queued.headers["Location"]

    def cancel_during_work(*_, **__):
        assert client.get(path, headers=owner).json()["status"] == "running"
        assert (
            client.post(f"{path}/cancel", headers=owner).json()["status"] == "cancelled"
        )
        return result

    monkeypatch.setattr(search_worker, "run_hybrid", cancel_during_work)
    assert search_worker.process_one()
    assert client.get(path, headers=owner).json()["run_id"] is None
    assert len(client.get("/api/v1/search-runs", headers=owner).json()) == 1
    assert outcomes == [("search_job_finished", {"status": "succeeded"})]


def test_search_history_preview_is_bounded_and_private(accounts):
    client, ((owner_id, owner, _), (other_id, other, _)) = accounts
    query = "DEMO " + "發明" * 80
    with engine.begin() as conn:
        for user_id, request in (
            (owner_id, Jsonb({"query": query})),
            (owner_id, Jsonb({})),
            (other_id, Jsonb({"query": "Other DEMO query"})),
        ):
            conn.exec_driver_sql(
                "INSERT INTO search_runs (user_id, request, settings) VALUES (%s, %s, '{}')",
                (user_id, request),
            )
    endpoint = "/api/v1/search-runs"
    assert client.get(endpoint).status_code == 401
    response = client.get(endpoint, headers=owner)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert {item["query_preview"] for item in response.json()} == {
        query[:99] + "…",
        None,
    }
    assert [
        item["query_preview"] for item in client.get(endpoint, headers=other).json()
    ] == ["Other DEMO query"]


def test_background_report_is_private_ephemeral_and_deleted_with_run(
    accounts, monkeypatch
):
    client, ((owner_id, owner, _), (_, other, _)) = accounts
    outcomes = []
    monkeypatch.setattr(
        report_jobs,
        "write_activity",
        lambda event, _, **info: outcomes.append((event, info)),
    )
    with engine.begin() as conn:
        run_id = conn.exec_driver_sql(
            """INSERT INTO search_runs (user_id, request, settings)
               VALUES (%s, '{"query":"DEMO"}', '{}') RETURNING id""",
            (owner_id,),
        ).scalar_one()
    reports = f"/api/v1/search-runs/{run_id}/reports"
    assert client.post(reports, headers=other).status_code == 404
    queued = client.post(reports, headers=owner)
    assert queued.status_code == 202
    path = queued.headers["Location"]
    assert client.post(reports, headers=owner).headers["Location"] == path
    assert client.get(path + "/pdf", headers=owner).status_code == 409
    assert client.get(path, headers=other).status_code == 404
    assert client.get(path + "/pdf", headers=other).status_code == 404

    def render(run, user):
        assert (run, user) == (run_id, owner_id)
        return b"%PDF-1.4\nDEMO"

    monkeypatch.setattr(report_jobs, "render_saved_report", render)
    assert report_jobs.process_one_report()
    assert outcomes == [("report_job_finished", {"status": "succeeded"})]
    assert client.get(path, headers=owner).json()["status"] == "succeeded"
    download = client.get(path + "/pdf", headers=owner)
    assert download.content == b"%PDF-1.4\nDEMO"
    assert download.headers["Cache-Control"] == "private, no-store"
    assert download.headers["Content-Type"] == "application/pdf"
    assert client.get(path + "/pdf", headers=other).status_code == 404

    with engine.begin() as conn:
        conn.exec_driver_sql(
            "UPDATE generated_reports SET finished_at = now() - interval '2 hours' WHERE run_id=%s",
            (run_id,),
        )
    assert client.get(path + "/pdf", headers=owner).status_code == 404
    assert (
        client.delete(f"/api/v1/search-runs/{run_id}", headers=owner).status_code == 204
    )
    with engine.connect() as conn:
        assert not conn.exec_driver_sql(
            "SELECT EXISTS (SELECT 1 FROM generated_reports WHERE run_id=%s)", (run_id,)
        ).scalar_one()


def test_ingestion_monitor_requires_an_operator_selected_account(accounts, monkeypatch):
    client, ((operator_id, operator, _), (_, other, _)) = accounts
    path = "/api/v1/admin/ingestion/jobs"
    assert client.get(path).status_code == 401
    monkeypatch.setenv("INGESTION_ADMIN_USER_IDS", str(operator_id))
    assert client.get("/api/v1/me", headers=operator).json()["can_monitor_ingestion"]
    assert not client.get("/api/v1/me", headers=other).json()["can_monitor_ingestion"]
    assert client.get(path, headers=other).status_code == 403
    response = client.get(path, headers=operator)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "private, no-store"
    assert isinstance(response.json(), list)
    with engine.begin() as conn:
        with pytest.raises(ProgrammingError) as error:
            conn.exec_driver_sql(
                "UPDATE ingestion_jobs SET stage = 'lexical' WHERE false"
            )
        assert isinstance(error.value.orig, InsufficientPrivilege)


def test_background_report_reclaims_stale_job_and_fences_old_worker(
    accounts, monkeypatch
):
    client, ((owner_id, owner, _), (_, other, _)) = accounts
    with engine.begin() as conn:
        run_id = conn.exec_driver_sql(
            """INSERT INTO search_runs (user_id, request, settings)
               VALUES (%s, '{"query":"DEMO"}', '{}') RETURNING id""",
            (owner_id,),
        ).scalar_one()
    endpoint = f"/api/v1/search-runs/{run_id}/reports"
    queued = client.post(endpoint, headers=owner)
    assert queued.status_code == 202
    path = queued.headers["Location"]
    report_id = UUID(queued.json()["id"])
    calls = []

    def render(run, user):
        assert (run, user) == (run_id, owner_id)
        calls.append(run)
        if len(calls) == 1:
            assert not report_jobs.process_one_report()
            with engine.begin() as conn:
                conn.exec_driver_sql(
                    """UPDATE generated_reports
                       SET started_at = now() - interval '7 minutes',
                           created_at = now() - interval '8 minutes' WHERE id = %s""",
                    (report_id,),
                )
            assert report_jobs.process_one_report()
            return b"%PDF-1.4\nDEMO obsolete worker"
        return b"%PDF-1.4\nDEMO recovered worker"

    monkeypatch.setattr(report_jobs, "render_saved_report", render)
    assert report_jobs.process_one_report()
    assert calls == [run_id, run_id]
    assert client.get(path, headers=owner).json()["status"] == "succeeded"
    assert (
        client.get(path + "/pdf", headers=owner).content
        == b"%PDF-1.4\nDEMO recovered worker"
    )
    assert client.get(path + "/pdf", headers=other).status_code == 404

    next_job = client.post(endpoint, headers=owner)
    next_id = UUID(next_job.json()["id"])
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """UPDATE generated_reports SET status = 'running',
               started_at = now() - interval '7 minutes',
               created_at = now() - interval '11 minutes' WHERE id = %s""",
            (next_id,),
        )
    assert not report_jobs.process_one_report()
    assert (
        client.get(next_job.headers["Location"], headers=owner).json()["status"]
        == "failed"
    )


def test_background_search_reclaims_stale_job_and_saves_once(accounts, monkeypatch):
    client, ((_, owner, _), (_, other, _)) = accounts
    queued = client.post(
        "/api/v1/search-jobs", headers=owner, json={"query": "DEMO recover"}
    )
    assert queued.status_code == 202
    path = queued.headers["Location"]
    job_id = UUID(queued.json()["id"])
    result = HybridSearchResults(
        items=[],
        tokenizer_version="DEMO",
        model_name="DEMO",
        model_digest="a" * 64,
        pipeline="DEMO",
        query_expansion_version="DEMO",
        rrf_k=60,
        candidate_limit=100,
        applied_feature_ids=[],
        reranker=None,
        limit=20,
        offset=0,
        has_more=False,
    )

    def superseded(request, *, full_snapshot):
        assert request.query == "DEMO recover" and full_snapshot
        assert not search_worker.process_one()
        with engine.begin() as conn:
            conn.exec_driver_sql(
                "UPDATE search_jobs SET started_at = started_at + interval '1 second' WHERE id = %s",
                (job_id,),
            )
        return result

    monkeypatch.setattr(search_worker, "run_hybrid", superseded)
    assert search_worker.process_one()
    state = client.get(path, headers=owner).json()
    assert state["status"] == "running" and state["run_id"] is None
    assert client.get("/api/v1/search-runs", headers=owner).json() == []
    assert client.get(path, headers=other).status_code == 404
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """UPDATE search_jobs SET started_at = now() - interval '7 minutes',
                created_at = now() - interval '8 minutes' WHERE id = %s""",
            (job_id,),
        )

    monkeypatch.setattr(search_worker, "run_hybrid", lambda *_args, **_kwargs: result)
    assert search_worker.process_one()
    state = client.get(path, headers=owner).json()
    assert state["status"] == "succeeded"
    [saved] = client.get("/api/v1/search-runs", headers=owner).json()
    assert saved["id"] == state["run_id"]
    detail = client.get(f"/api/v1/search-runs/{saved['id']}", headers=owner).json()
    assert detail["request"]["query"] == "DEMO recover"

    expired = client.post(
        "/api/v1/search-jobs", headers=owner, json={"query": "DEMO expires"}
    )
    expired_id = UUID(expired.json()["id"])
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """UPDATE search_jobs SET status = 'running',
                started_at = now() - interval '7 minutes',
                created_at = now() - interval '11 minutes' WHERE id = %s""",
            (expired_id,),
        )
    assert not search_worker.process_one()
    state = client.get(expired.headers["Location"], headers=owner).json()
    assert state["status"] == "failed"
    assert state["error_code"] == "SEARCH_JOB_EXPIRED"
    with engine.connect() as conn:
        assert conn.exec_driver_sql(
            "SELECT request IS NULL FROM search_jobs WHERE id = %s", (expired_id,)
        ).scalar_one()
