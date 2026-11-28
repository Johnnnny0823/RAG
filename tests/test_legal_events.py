from datetime import date
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock

from pytest import mark, raises

from services.ingestion import legal_refresh
from services.ingestion import legal_events
from services.ingestion.artifacts import LocalObjectStore
from services.ingestion.legal_events import parse_events


def test_replay_checks_local_integrity_and_continues_other_issues(
    monkeypatch, tmp_path
):
    store = LocalObjectStore(tmp_path)
    valid = store.put(b"verified DEMO fixture")
    rows = [
        SimpleNamespace(
            batch_key="053032",
            source_locator=legal_events.archive_url("115", "053032", "sud08"),
            checksum=valid.checksum,
            object_key=valid.object_key,
            size_bytes=valid.size_bytes + 1,
        ),
        SimpleNamespace(
            batch_key="053033",
            source_locator=legal_events.archive_url("115", "053033", "sud24"),
            checksum=valid.checksum,
            object_key=valid.object_key,
            size_bytes=valid.size_bytes,
        ),
    ]
    connection = Mock()
    connection.exec_driver_sql.return_value.all.return_value = rows
    monkeypatch.setattr(legal_events.engine, "connect", lambda: nullcontext(connection))
    importer = Mock(return_value={"new_events": 2})
    monkeypatch.setattr(legal_events, "import_events", importer)

    assert legal_events.replay_stored_events(store) == {
        "replayed_artifacts": 1,
        "failed_artifacts": 1,
        "new_events": 2,
    }
    importer.assert_called_once_with(
        b"verified DEMO fixture", store, "115", "053033", "sud24"
    )


# Synthetic event for parser regression coverage.
EXTINGUISHMENT = b"""<!DOCTYPE Sud08Dataset SYSTEM "sud08.dtd"[]>
<Sud08Dataset xmlns="http://tempuri.org/Sud08Dataset.xsd">
  <sud08><cerno>I999999</cerno><aplno>000000001</aplno><volno>53</volno><isuno>33</isuno>
    <extdt>115/02/21</extdt><extson>fixture reason</extson><patentee>fixture name</patentee>
  </sud08>
  <sud08><cerno>2999999</cerno><volno>53</volno><isuno>33</isuno></sud08>
</Sud08Dataset>"""

CORRECTION = b"""
<Sud24Dataset xmlns="http://tempuri.org/Sud24Dataset.xsd">
  <sud24><orgpatno>I999999</orgpatno><orgaplno>000000001</orgaplno><volno>53</volno><isuno>33</isuno>
    <fixfld>fixture field</fixfld><fixcont>fixture private field</fixcont>
  </sud24>
</Sud24Dataset>"""


def test_extinguishment_date_comes_from_source_and_legacy_numbers_are_skipped():
    [event] = parse_events(EXTINGUISHMENT, "053033", "sud08")
    assert event.application_no == "000000001" and event.certificate_no == "I999999"
    assert event.effective_on == date(2026, 2, 21)
    assert event.detail == "fixture reason"
    assert event.record_locator.endswith("*[local-name()='sud08'][1]")


def test_modern_utility_model_and_derived_design_events_keep_their_identities():
    utility = EXTINGUISHMENT.replace(b"I999999", b"M999999")
    [extinction] = parse_events(utility, "053033", "sud08")
    assert extinction.certificate_no == "M999999"
    assert extinction.effective_on == date(2026, 2, 21)

    derived = CORRECTION.replace(b"I999999", b"D999999").replace(
        b"000000001", b"000300001D01"
    )
    [correction] = parse_events(derived, "053033", "sud24")
    assert correction.application_no == "000300001D01"
    assert correction.certificate_no == "D999999"


def test_correction_exposes_only_the_corrected_field_and_has_no_assumed_date():
    [event] = parse_events(CORRECTION, "053033", "sud24")
    assert event.detail == "fixture field"
    assert event.effective_on is None


def test_rejects_wrong_issue_and_unrecognized_dtd():
    with raises(ValueError, match="different gazette issue"):
        parse_events(CORRECTION, "053032", "sud24")
    with raises(ValueError, match="DOCTYPE"):
        parse_events(
            EXTINGUISHMENT.replace(b"sud08.dtd", b"other.dtd"), "053033", "sud08"
        )


@mark.parametrize("disagree", [None, "index", "correction"])
def test_latest_legal_refresh_requires_index_and_category_agreement(
    monkeypatch, tmp_path, disagree
):
    index = b"""<SundryData total-count="2">
    <Sundry aplno="000000001" cerno="I999999" sudtype="sud08"/>
    <Sundry aplno="000000001" cerno="I999999" sudtype="sud24"/>
    </SundryData>"""
    calls = []
    monkeypatch.setattr(legal_refresh, "download_legal_index", lambda: index)
    monkeypatch.setattr(
        legal_refresh, "list_archive_issues", lambda *_: ["053033", "053034"]
    )

    def download(url):
        if url.endswith("/PatentIsuModXML_053033/index.xml") and disagree != "index":
            return index
        if url.endswith("/index.xml"):
            return b"different archived index"
        if url.endswith("/sud08.xml"):
            return EXTINGUISHMENT
        if url.endswith("/sud24.xml"):
            return (
                CORRECTION.replace(b"000000001", b"000000002")
                if disagree
                else CORRECTION
            )
        raise AssertionError(url)

    def imported(payload, store, year, issue, event_type):
        assert (year, issue) == ("115", "053033")
        calls.append(event_type)
        return {"new_events": 1}

    monkeypatch.setattr(legal_refresh, "download_ftps_xml", download)
    monkeypatch.setattr(legal_refresh, "import_events", imported)
    store = LocalObjectStore(tmp_path)
    if disagree:
        with raises(ValueError, match="did not match|disagrees"):
            legal_refresh.refresh("115", store, apply=True)
        assert not calls
        assert not list(tmp_path.iterdir())
    else:
        preview = legal_refresh.refresh("115", store, apply=False)
        assert preview["issue"] == "053033"
        assert preview["events"]["sud08"]["invention_events"] == 1
        assert not list(tmp_path.iterdir())
        assert not calls
        assert legal_refresh.refresh("115", store, apply=True)["events"] == {
            "sud08": {"new_events": 1},
            "sud24": {"new_events": 1},
        }
        assert calls == ["sud08", "sud24"]


def test_archived_legal_refresh_requires_category_records_from_the_selected_issue(
    monkeypatch, tmp_path
):
    index = b'<SundryData total-count="1"><Sundry aplno="000000001" cerno="I999999" sudtype="sud08"/></SundryData>'
    sources = {
        "ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053032/index.xml": index,
        "ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053032/sud08.xml": EXTINGUISHMENT,
    }
    monkeypatch.setattr(legal_refresh, "download_ftps_xml", sources.__getitem__)
    with raises(ValueError, match="different gazette issue"):
        legal_refresh.refresh(
            "115", LocalObjectStore(tmp_path), apply=True, issue="053032"
        )
    assert not list(tmp_path.iterdir())
