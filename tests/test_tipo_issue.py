import pytest

from services.ingestion.issue_index import parse_issue_index
from services.ingestion.specification import DOCTYPE, parse_specification

# DEMO fixture matching the observed issue index and specification structure.
INDEX = """<tw-patent-applications total-count="1">
  <tw-patent-application no="1" publication-number="000000002">
    <tw-bibliographic-data-application>
      <volno>24</volno><isuno>19</isuno>
      <publication-reference><document-id><doc-number>000000002</doc-number></document-id></publication-reference>
      <application-reference><document-id><doc-number>000000001</doc-number></document-id></application-reference>
      <invention-title><chinese-title>DEMO</chinese-title></invention-title>
      <classification-ipc><main-classification edition="raw">A01B1/00</main-classification></classification-ipc>
    </tw-bibliographic-data-application>
    <description><isu-abst lang="tw"><p>合成摘要</p></isu-abst></description>
  </tw-patent-application>
</tw-patent-applications>""".encode()

SPEC = (
    DOCTYPE
    + """
<invention-specification application-num="000000001" dtd-version="A103.1.0">
  <description><technical-field><p>測試<sup>2</sup>文字。</p></technical-field></description>
  <claims><claim num="1" dependency="independent-claim"><claim-text>合成請求項</claim-text></claim></claims>
</invention-specification>""".encode()
)


def test_issue_index_extracts_provenance_and_bibliography():
    records, issues = parse_issue_index(INDEX, expected_issue="024019")
    assert not issues
    [record] = records
    assert record.application_no == "000000001"
    assert record.publication_no == "000000002"
    assert record.title_zh == "DEMO"
    assert record.abstract_zh == "合成摘要"
    assert record.ipc == [("A01B1/00", "raw")]
    assert record.locator == "/tw-patent-applications/tw-patent-application[1]"


def test_issue_index_rejects_a_different_issue():
    with pytest.raises(ValueError, match="requested issue"):
        parse_issue_index(INDEX, expected_issue="024020")


def test_specification_keeps_exact_text_and_locator():
    [section], [claim] = parse_specification(SPEC, "000000001")
    assert section.text == "測試2文字。"
    assert section.locator.endswith("/technical-field/p[1]")
    assert claim.text == "合成請求項"
    assert claim.locator.endswith("/claims/claim[1]")
    assert claim.independent is True


def test_specification_rejects_wrong_application_and_untrusted_doctype():
    with pytest.raises(ValueError, match="application number"):
        parse_specification(SPEC, "000000002")
    with pytest.raises(ValueError, match="DOCTYPE"):
        parse_specification(
            SPEC.replace(
                DOCTYPE, b'<!DOCTYPE invention-specification [<!ENTITY e "x">]>'
            ),
            "000000001",
        )
