from datetime import date
import json

import pytest

from services.ingestion import latest_publication
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


def test_design_gazette_classification_is_bound_to_the_certificate_and_edition():
    # Synthetic fixture modeling a grant bibliography with LOC edition metadata.
    design = (
        PUBLICATION.replace(b"tw-patent-application", b"tw-patent-grant")
        .replace(b"tw-bibliographic-data-application", b"tw-bibliographic-data-grant")
        .replace(b"invention-public", b"design")
        .replace(
            b"<doc-number>000000001</doc-number>", b"<doc-number>D000001</doc-number>"
        )
        .replace(
            b"</publication-reference>",
            b"""</publication-reference>
            <certificate-number><document-id><doc-number>D000001</doc-number></document-id></certificate-number>
            <classification-locarno><main-classification edition="15">13-99</main-classification></classification-locarno>""",
        )
    )
    record = parse_gazette(design, "grant", "115", "024019", include_other_grants=True)[
        "D000001"
    ]
    assert record.loc == (("13-99", "15"),)
    assert record.application_no == "000000002"
    derived = design.replace(b"000000002", b"000000002D01")
    assert (
        parse_gazette(derived, "grant", "115", "024019", include_other_grants=True)[
            "D000001"
        ].application_no
        == "000000002D01"
    )
    with pytest.raises(ValueError, match="application type disagree"):
        parse_gazette(
            design.replace(b'"design"', b'"model"'),
            "grant",
            "115",
            "024019",
            include_other_grants=True,
        )


def test_latest_issue_previews_verified_dates_and_applies_only_after_import(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(
        latest_publication, "download_publication_index", lambda: b"index"
    )
    monkeypatch.setattr(
        latest_publication, "discover_issue", lambda data: ("024019", 1)
    )

    def download(url):
        assert url.endswith("/115/PatentPubRegXMLB_024019/pubinvention.xml")
        return PUBLICATION

    monkeypatch.setattr(latest_publication, "download_ftps_xml", download)
    calls = []

    def pipeline(*args, **kwargs):
        calls.append("patents")
        return pipeline_status

    def apply(data, store, stage, year, issue):
        assert (data, stage, year, issue) == (
            PUBLICATION,
            "publication",
            "115",
            "024019",
        )
        calls.append("dates")
        return {"matched_versions": 1}

    monkeypatch.setattr(latest_publication, "run_pipeline", pipeline)
    monkeypatch.setattr(latest_publication, "apply_dates", apply)
    options = ["--gazette-year", "115", "--objects", str(tmp_path)]
    assert latest_publication.main(options) == 0
    assert json.loads(capsys.readouterr().out)["gazette_sha256"]
    assert not calls

    pipeline_status = 1
    assert latest_publication.main([*options, "--apply"]) == 1
    assert calls == ["patents"]

    pipeline_status = 0
    assert latest_publication.main([*options, "--apply"]) == 0
    assert calls == ["patents", "patents", "dates"]

    monkeypatch.setattr(
        latest_publication,
        "download_ftps_xml",
        lambda url: PUBLICATION.replace(b"<isuno>19", b"<isuno>18"),
    )
    with pytest.raises(SystemExit) as error:
        latest_publication.main([*options, "--apply"])
    assert error.value.code == 1
    assert calls == ["patents", "patents", "dates"]
