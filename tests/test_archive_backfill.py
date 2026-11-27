import json

import pytest

from services.ingestion import archive_backfill, latest_publication


OPTIONS = [
    "--stage",
    "grant",
    "--year",
    "115",
    "--from-issue",
    "053031",
    "--through-issue",
    "053033",
    "--limit",
    "2",
]


def test_backfill_previews_only_verified_range_and_stops_on_import_failure(
    monkeypatch, tmp_path, capsys
):
    def list_issues(stage, year):
        assert (stage, year) == ("grant", "115")
        return ["053030", "053031", "053032", "053033"]

    calls = []

    def import_one(options):
        assert options[options.index("--limit") + 1] == "2"
        assert "--grants" in options and "--apply" in options
        assert options[options.index("--archive-year") + 1] == "115"
        assert options[options.index("--gazette-year") + 1] == "115"
        calls.append(options[-1])
        return int(options[-1] == "053032")

    monkeypatch.setattr(archive_backfill, "list_archive_issues", list_issues)
    monkeypatch.setattr(archive_backfill, "import_one", import_one)
    assert archive_backfill.main(OPTIONS) == 0
    assert json.loads(capsys.readouterr().out)["issues"] == [
        "053031",
        "053032",
        "053033",
    ]
    assert not calls
    options = [*OPTIONS, "--fulltext", "--dates", "--apply", "--objects", str(tmp_path)]
    assert archive_backfill.main(options) == 1
    assert calls == ["053031", "053032"]


def test_backfill_rejects_incomplete_range_before_import(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        archive_backfill, "list_archive_issues", lambda *_: ["053031", "053033"]
    )

    def unexpected_import(options):
        pytest.fail(f"Attempted import with missing issue: {options[-1]}")

    monkeypatch.setattr(archive_backfill, "import_one", unexpected_import)
    with pytest.raises(SystemExit) as error:
        archive_backfill.main([*OPTIONS, "--apply", "--objects", str(tmp_path)])
    assert error.value.code == 1
    assert "Issues missing from the archive: 053032" in capsys.readouterr().err


def test_archived_index_must_contain_the_requested_issue(monkeypatch, capsys):
    def download(url):
        assert (
            url
            == "ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024018/index.xml"
        )
        return b"index"

    monkeypatch.setattr(latest_publication, "download_ftps_xml", download)
    monkeypatch.setattr(latest_publication, "discover_issue", lambda _: ("024019", 1))
    with pytest.raises(SystemExit) as error:
        latest_publication.main(["--archive-issue", "024018", "--issue-year", "115"])
    assert error.value.code == 1
    assert "Archive index does not match the requested issue" in capsys.readouterr().err


def test_design_backfill_passes_the_grant_type_to_each_archived_issue(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(
        archive_backfill,
        "list_archive_issues",
        lambda *_: ["053031", "053032", "053033"],
    )
    calls = []

    def import_one(options):
        assert "--grants" in options
        assert options[options.index("--grant-type") + 1] == "design"
        calls.append(options[-1])
        return 0

    monkeypatch.setattr(archive_backfill, "import_one", import_one)
    options = [*OPTIONS, "--grant-type", "design"]
    assert archive_backfill.main(options) == 0
    assert json.loads(capsys.readouterr().out)["grant_type"] == "design"
    assert calls == []
    assert archive_backfill.main([*options, "--apply", "--objects", str(tmp_path)]) == 0
    assert calls == ["053031", "053032", "053033"]
