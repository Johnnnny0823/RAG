from datetime import date

import pytest

from services.ingestion.patentpub import parse_patentpub

# DEMO fixture using the official PatentPub element names and synthetic values.
RECORD = """
<patentcontent>
  <publication-reference><notice-no>000000002</notice-no><notice-date>2025/03/04</notice-date></publication-reference>
  <application-reference><appl-no>000000001</appl-no><appl-date>2024/01/02</appl-date></application-reference>
  <patent-title><patent-name-chinese>DEMO 合成文件</patent-name-chinese></patent-title>
  <parties><applicants><applicant><chinese-name>DEMO</chinese-name><address>ignored</address></applicant></applicants></parties>
  <classification-ipc><ipc><ipc-full>A01B 1/00</ipc-full><ipc-version>2025.01</ipc-version></ipc></classification-ipc>
</patentcontent>
"""


def page(*records):
    return (
        f'<API><status>ok</status><tw-patent-pub page-count="{len(records)}">'
        + "".join(records)
        + "</tw-patent-pub></API>"
    ).encode()


def test_patentpub_preserves_identifier_fields_and_record_locator():
    records, issues = parse_patentpub(page(RECORD))
    assert not issues
    [record] = records
    assert record.application_no == "000000001"
    assert record.publication_no == "000000002"
    assert record.filing_date == date(2024, 1, 2)
    assert record.publication_date == date(2025, 3, 4)
    assert record.title_zh == "DEMO 合成文件"
    assert record.applicants == [{"zh": "DEMO"}]
    assert record.ipc == [("A01B 1/00", "2025.01")]
    assert record.locator == "/API/tw-patent-pub/patentcontent[1]"


def test_patentpub_quarantines_bad_row_and_preserves_good_rows():
    invalid = RECORD.replace("000000001", "bad")
    records, issues = parse_patentpub(page(invalid, RECORD))
    assert len(records) == len(issues) == 1
    assert issues[0].locator.endswith("[1]")
    assert records[0].locator.endswith("[2]")
    assert records[0].source_hash == parse_patentpub(page(RECORD))[0][0].source_hash


def test_patentpub_rejects_dtd_before_entity_expansion():
    with pytest.raises(ValueError, match="DOCTYPE"):
        parse_patentpub(b'<!DOCTYPE API [<!ENTITY bomb "expanded">]>' + page(RECORD))


def test_patentpub_rejects_failed_or_truncated_page():
    with pytest.raises(ValueError, match="successful"):
        parse_patentpub(page(RECORD).replace(b">ok<", b">failed<"))
    with pytest.raises(ValueError, match="count"):
        parse_patentpub(page(RECORD).replace(b'page-count="1"', b'page-count="2"'))
