from services.ingestion import refresh_publications


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
