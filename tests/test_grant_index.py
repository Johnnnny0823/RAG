import pytest

from services.ingestion.artifacts import MAX_XML_BYTES
from services.ingestion.grant_index import (
    discover_grant_issue,
    parse_grant,
    parse_selected_grants,
)
from services.ingestion.patentpub import parse_xml

GRANT = b"""<tw-patent-grants total-count="1">
  <tw-patent-grant certificate-number="I000001">
    <tw-bibliographic-data-grant>
      <volno>53</volno><isuno>28</isuno>
      <publication-reference><document-id><doc-number>I000001</doc-number></document-id></publication-reference>
      <certificate-number><document-id><doc-number>I000001</doc-number></document-id></certificate-number>
      <application-reference appl-type="invention"><document-id><doc-number>000000001</doc-number></document-id></application-reference>
      <invention-title><english-title>DEMO</english-title></invention-title>
    </tw-bibliographic-data-grant>
    <claims><claim num="1"><p>DEMO exact text</p></claim></claims>
  </tw-patent-grant>
</tw-patent-grants>"""


def test_grant_preserves_separate_certificate_and_application_identifiers():
    assert discover_grant_issue(GRANT) == ("053028", ["I000001"])
    grant, [claim] = parse_grant(GRANT, "053028", "I000001")
    assert grant.publication_no == "I000001"
    assert grant.application_no == "000000001"
    assert claim.text == "DEMO exact text"
    assert claim.independent is None
    assert claim.locator == "/tw-patent-grants/tw-patent-grant[1]/claims/claim[1]"
    with pytest.raises(ValueError, match="requested issue"):
        parse_grant(GRANT, "053029", "I000001")


def test_selected_grants_bind_each_publication_to_its_own_claims():
    first = GRANT.split(b"<tw-patent-grant ", 1)[1].split(b"</tw-patent-grants>", 1)[0]
    second = (
        first.replace(b"I000001", b"I000002")
        .replace(b"000000001", b"000000002")
        .replace(b"DEMO exact text", b"Second DEMO")
    )
    combined = (
        b'<tw-patent-grants total-count="2"><tw-patent-grant '
        + first
        + b"<tw-patent-grant "
        + second
        + b"</tw-patent-grants>"
    )
    parsed = parse_selected_grants(combined, "053028", ["I000002", "I000001"])
    assert [(record.publication_no, claims[0].text) for record, claims in parsed] == [
        ("I000002", "Second DEMO"),
        ("I000001", "DEMO exact text"),
    ]
    assert parsed[0][1][0].locator.endswith("tw-patent-grant[2]/claims/claim[1]")
    with pytest.raises(ValueError, match="Missing selected"):
        parse_selected_grants(combined, "053028", ["I000001", "I000003"])


def test_large_grant_issue_is_accepted_without_raising_the_individual_xml_limit():
    issue = GRANT.ljust(MAX_XML_BYTES + 1, b" ")

    grant, claims = parse_grant(issue, "053028", "I000001")

    assert grant.publication_no == "I000001" and len(claims) == 1
    with pytest.raises(ValueError, match="exceeds the size limit"):
        parse_xml(issue)
