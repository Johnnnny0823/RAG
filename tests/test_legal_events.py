from datetime import date

from pytest import raises

from services.ingestion.legal_events import parse_events

# Synthetic event for parser regression coverage.
EXTINGUISHMENT = b"""<!DOCTYPE Sud08Dataset SYSTEM "sud08.dtd"[]>
<Sud08Dataset xmlns="http://tempuri.org/Sud08Dataset.xsd">
  <sud08><cerno>I999999</cerno><aplno>000000001</aplno><volno>53</volno><isuno>33</isuno>
    <extdt>115/02/21</extdt><extson>fixture reason</extson><patentee>fixture name</patentee>
  </sud08>
  <sud08><cerno>M999999</cerno><volno>53</volno><isuno>33</isuno></sud08>
</Sud08Dataset>"""

CORRECTION = b"""
<Sud24Dataset xmlns="http://tempuri.org/Sud24Dataset.xsd">
  <sud24><orgpatno>I999999</orgpatno><orgaplno>000000001</orgaplno><volno>53</volno><isuno>33</isuno>
    <fixfld>fixture field</fixfld><fixcont>fixture private field</fixcont>
  </sud24>
</Sud24Dataset>"""


def test_extinguishment_date_comes_from_source_and_other_patent_kinds_are_skipped():
    [event] = parse_events(EXTINGUISHMENT, "053033", "sud08")
    assert event.application_no == "000000001" and event.certificate_no == "I999999"
    assert event.effective_on == date(2026, 2, 21)
    assert event.detail == "fixture reason"
    assert event.record_locator.endswith("*[local-name()='sud08'][1]")


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
