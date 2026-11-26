from contextlib import nullcontext
from unittest.mock import Mock

from services.ingestion import archive_refresh, refresh_publications


def test_publication_refresh_retries_failure_then_returns_to_normal_interval(
    monkeypatch,
):
    clock = 0
    started = []

    def refresh(options):
        assert options == ["--apply"]
        started.append(clock)
        if len(started) == 1:
            raise SystemExit(1)
        return 0

    def advance(seconds):
        nonlocal clock
        clock += seconds

    monkeypatch.setattr(refresh_publications, "refresh_once", refresh)
    monkeypatch.setattr(refresh_publications, "monotonic", lambda: clock)
    monkeypatch.setattr(refresh_publications, "sleep", advance)
    refresh_publications.serve(
        ["--apply"],
        interval=86400,
        retry_interval=900,
        should_stop=lambda: len(started) >= 3,
    )
    assert started == [0, 900, 87300]


def test_publication_failure_does_not_skip_the_grant_update(monkeypatch):
    runs = []

    def refresh(options):
        runs.append(options)
        if "--grants" not in options:
            raise SystemExit(1)
        return 0

    monkeypatch.setattr(refresh_publications, "refresh_once", refresh)
    refresh_publications.serve(
        ["--apply"], 86400, 900, lambda: len(runs) == 2, include_grants=True
    )
    assert runs == [["--apply"], ["--apply", "--grants"]]


def test_legal_refresh_still_runs_after_publication_failure(monkeypatch):
    def fail(options):
        raise SystemExit(1)

    completed = []
    monkeypatch.setattr(refresh_publications, "refresh_once", fail)
    monkeypatch.setattr(refresh_publications, "refresh_legal", completed.append)
    refresh_publications.serve(
        ["--apply"], 86400, 900, lambda: bool(completed), legal_year="115"
    )
    assert completed == [["--year", "115", "--apply"]]


def test_legal_history_keeps_the_latest_gazette_refresh(monkeypatch):
    completed = []

    def recover(stage, year, first, options, max_issues, should_stop):
        completed.append((stage, year, first, options, max_issues))
        raise SystemExit(1)

    monkeypatch.setattr(refresh_publications, "refresh_once", lambda _: 0)
    monkeypatch.setattr(refresh_publications, "refresh_archive", recover)
    monkeypatch.setattr(refresh_publications, "refresh_legal", completed.append)
    refresh_publications.serve(
        ["--apply"],
        86400,
        900,
        lambda: len(completed) == 2,
        legal_year="115",
        legal_from="053032",
    )
    assert completed == [
        ("legal", "115", "053032", ["--apply"], 2),
        ["--year", "115", "--apply"],
    ]


def test_archive_resumes_only_successful_issues_for_the_same_configuration(monkeypatch):
    checkpoint_rows = set()
    conn = Mock()

    def execute(query, params):
        if "SELECT" in query:
            return Mock(
                scalars=lambda: [row[3] for row in checkpoint_rows if row[:3] == params]
            )
        checkpoint_rows.add(params)

    calls = []

    def import_one(options):
        calls.append(options[-1])
        return int(calls == ["053031", "053032"])

    conn.exec_driver_sql.side_effect = execute
    monkeypatch.setattr(archive_refresh.engine, "connect", lambda: nullcontext(conn))
    monkeypatch.setattr(archive_refresh.engine, "begin", lambda: nullcontext(conn))
    monkeypatch.setattr(
        archive_refresh,
        "list_archive_issues",
        lambda *_: ["053031", "053032", "053034"],
    )
    monkeypatch.setattr(archive_refresh, "import_one", import_one)
    args = ("grant", "115", "053031")
    options = ["--apply", "--grants", "--limit", "1"]
    assert archive_refresh.refresh_archive(*args, options, 1, lambda: False)
    assert archive_refresh.refresh_archive(*args, options, 2, lambda: False)
    assert archive_refresh.refresh_archive(*args, options, 2, lambda: False)
    assert archive_refresh.refresh_archive(*args, options, 2, lambda: False)
    assert calls == ["053031", "053032", "053032"]
    assert {row[3] for row in checkpoint_rows} == {"053031", "053032"}

    assert archive_refresh.refresh_archive(
        *args, [*options[:-1], "2"], 1, lambda: False
    )
    assert calls[-1] == "053031"
    assert len(checkpoint_rows) == 3
