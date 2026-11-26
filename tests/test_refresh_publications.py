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
