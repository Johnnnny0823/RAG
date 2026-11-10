"""Exercise the migrated PostgreSQL schema and API with an isolated database."""

import hashlib
import os
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from psycopg.errors import ForeignKeyViolation
from sqlalchemy.exc import IntegrityError

from services.api.db import engine
from services.api.main import app

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
    with engine.connect() as conn:
        assert (
            conn.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one()
            == expected
        )
        assert (
            conn.exec_driver_sql(
                "SELECT '[1, 2]'::vector <-> '[4, 6]'::vector"
            ).scalar_one()
            == 5
        )
    with TestClient(app) as client:
        assert client.get("/api/v1/ready").json() == {"status": "ready"}


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
        # Age the failures instead of waiting for the window to pass.
        conn.exec_driver_sql(
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
