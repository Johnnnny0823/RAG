from datetime import date

import pytest

from services.ingestion.gazette_dates import parse_gazette, roc_date

# Synthetic excerpts model element structure only; these identifiers are fixtures.
PUBLICATION = b"""
<tw-patent-applications total-count="1"><tw-patent-application>
  <tw-bibliographic-data-application>
    <volno>24</volno><isuno>19</isuno>
    <publication-reference><document-id><doc-number>000000001</doc-number>
      <date>115/10/01</date></document-id></publication-reference>
    <application-reference appl-type="invention-public"><document-id>
      <doc-number>000000002</doc-number><date>113/09/06</date>
    </document-id></application-reference>
  </tw-bibliographic-data-application>
</tw-patent-application></tw-patent-applications>
"""


def test_extract_dates_with_document_identity_and_locator():
    record = parse_gazette(PUBLICATION, "publication", "115", "024019")["000000001"]
    assert record.application_no == "000000002"
    assert record.filing_date == date(2024, 9, 6)
    assert record.publication_date == date(2026, 10, 1)
    assert (
        record.locator
        == "/tw-patent-applications/tw-patent-application[1]/tw-bibliographic-data-application"
    )


@pytest.mark.parametrize(
    ("source", "stage", "year", "issue"),
    [
        (PUBLICATION, "publication", "115", "024018"),
        (PUBLICATION, "publication", "114", "024019"),
        (PUBLICATION, "grant", "115", "024019"),
        (
            b"<!DOCTYPE tw-patent-applications>" + PUBLICATION,
            "publication",
            "115",
            "024019",
        ),
    ],
)
def test_reject_gazette_from_wrong_issue_or_with_doctype(source, stage, year, issue):
    with pytest.raises(ValueError):
        parse_gazette(source, stage, year, issue)


def test_roc_date_uses_the_real_calendar():
    assert roc_date("113/02/29") == date(2024, 2, 29)
    with pytest.raises(ValueError):
        roc_date("114/02/29")
