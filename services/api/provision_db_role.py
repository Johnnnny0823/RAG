"""Provision the runtime database login after schema migrations."""

import os

import psycopg
from psycopg import sql

API_ROLE = "patentscope_api"
CORPUS_TABLES = (
    "source_datasets",
    "ingestion_batches",
    "ingestion_artifacts",
    "ingestion_jobs",
    "patent_applications",
    "patent_documents",
    "patent_legal_events",
    "gazette_pdf_pages",
    "document_artifacts",
    "patent_classifications",
    "patent_priorities",
    "patent_sections",
    "patent_claims",
    "claim_dependencies",
    "patent_lexical_chunks",
    "patent_embedding_models",
    "patent_dense_chunks",
)
RESEARCH_GRANTS = {
    # PostgreSQL requires UPDATE on at least one column for SELECT FOR UPDATE.
    "users": "SELECT, INSERT, DELETE, UPDATE (id)",
    "auth_sessions": "SELECT, INSERT, DELETE",
    "login_failures": "SELECT, INSERT, DELETE",
    "projects": "SELECT, INSERT, UPDATE, DELETE",
    "search_runs": "SELECT, INSERT, UPDATE, DELETE",
    "search_jobs": "SELECT, INSERT, UPDATE, DELETE",
    "generated_reports": "SELECT, INSERT, UPDATE, DELETE",
    "search_run_candidates": "SELECT, INSERT",
    "search_run_comparisons": "SELECT, INSERT",
    "saved_patents": "SELECT, INSERT, UPDATE, DELETE",
    "sessions": "SELECT, INSERT, DELETE, UPDATE (id)",
    "messages": "SELECT, INSERT",
    "audit_logs": "SELECT, INSERT",
}


def provision(password: str) -> None:
    role = sql.Identifier(API_ROLE)
    with psycopg.connect(connect_timeout=5) as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT rolcanlogin AND NOT (rolsuper OR rolcreaterole OR rolcreatedb
                       OR rolreplication OR rolbypassrls)
                      AND NOT EXISTS (SELECT 1 FROM pg_auth_members WHERE member = r.oid)
               FROM pg_roles r WHERE rolname = %s""",
            (API_ROLE,),
        )
        existing = cursor.fetchone()
        if existing is None:
            cursor.execute(sql.SQL("CREATE ROLE {} LOGIN").format(role))
        elif not existing[0]:
            raise ValueError("Existing patentscope_api role has unexpected attributes")

        verifier = conn.pgconn.encrypt_password(
            password.encode(), API_ROLE.encode(), b"scram-sha-256"
        ).decode("ascii")
        cursor.execute(
            sql.SQL("ALTER ROLE {} PASSWORD {}").format(role, sql.Literal(verifier))
        )
        cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(role))
        for table, privileges in (
            *((table, "SELECT") for table in CORPUS_TABLES),
            *RESEARCH_GRANTS.items(),
        ):
            cursor.execute(
                sql.SQL("GRANT {} ON TABLE {} TO {}").format(
                    sql.SQL(privileges), sql.Identifier("public", table), role
                )
            )


def main() -> None:
    password = os.environ.get("API_DB_PASSWORD")
    if not password or password == os.environ.get("PGPASSWORD"):
        raise SystemExit("Set a separate API_DB_PASSWORD before starting the API")
    try:
        provision(password)
    except psycopg.Error as error:
        # A database error can contain the password statement. Report only SQLSTATE.
        raise SystemExit(
            f"API role provisioning failed (SQLSTATE {error.sqlstate})"
        ) from None
    except ValueError as error:
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    main()
