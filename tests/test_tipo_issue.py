import pytest

from services.ingestion import latest_publication
from services.ingestion.issue_index import discover_issue, parse_issue_index
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


def test_latest_issue_rejects_mixed_versions_and_incomplete_index():
    assert discover_issue(INDEX) == ("024019", 1)
    second = (
        INDEX.split(b'<tw-patent-application no="1"')[1]
        .split(b"</tw-patent-applications>")[0]
        .replace(b"<isuno>19</isuno>", b"<isuno>20</isuno>")
    )
    mixed = INDEX.replace(b'total-count="1"', b'total-count="2"').replace(
        b"</tw-patent-applications>",
        b'<tw-patent-application no="2"' + second + b"</tw-patent-applications>",
    )
    with pytest.raises(ValueError, match="single nonempty issue"):
        discover_issue(mixed)
    with pytest.raises(ValueError, match="complete TIPO issue index"):
        discover_issue(INDEX.replace(b'total-count="1"', b'total-count="2"'))


def test_latest_fulltext_requires_valid_manifest_and_reports_partial_exit(
    monkeypatch, tmp_path
):
    manifest = b"""<tw-patent-applications total-count="1">
      <tw-patent-application publication-number="000000002">
        <specification-files xml-file="/InventionPubXML_024019/2419000000002/000000001-DEMO.xml"/>
      </tw-patent-application>
    </tw-patent-applications>"""
    sources = []
    applied = []
    monkeypatch.setattr(latest_publication, "download_publication_index", lambda: INDEX)

    def download(url):
        sources.append(url)
        return manifest

    def pipeline(args, mode, **options):
        assert args.index.read_bytes() == INDEX
        assert args.manifest.read_bytes() == manifest
        assert args.manifest_url == sources[-1]
        assert args.batch == "024019" and mode == "lexical"
        assert options["require_complete"] is True
        applied.append(True)
        return 1

    monkeypatch.setattr(latest_publication, "download_ftps_xml", download)
    monkeypatch.setattr(latest_publication, "run_pipeline", pipeline)
    monkeypatch.setattr("sys.argv", ["latest_publication", "--archive-year", "115"])
    assert latest_publication.main() == 0
    assert not applied
    monkeypatch.setattr(
        "sys.argv",
        [
            "latest_publication",
            "--archive-year",
            "115",
            "--apply",
            "--objects",
            str(tmp_path),
        ],
    )
    assert latest_publication.main() == 1
    assert applied == [True]
    assert (
        sources
        == [
            "ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/index_all.xml"
        ]
        * 2
    )


def test_specification_keeps_exact_text_and_locator():
    [section], [claim] = parse_specification(SPEC, "000000001")
    assert section.text == "測試2文字。"
    assert section.locator.endswith("/technical-field/p[1]")
    assert claim.text == "合成請求項"
    assert claim.locator.endswith("/claims/claim[1]")
    assert claim.independent is True


def test_grant_specification_requires_its_own_document_format():
    grant = SPEC.replace(b"invention-specification", b"specification")
    [section], [claim] = parse_specification(grant, "000000001", grant_number="I000001")
    assert section.locator == "/specification/description/technical-field/p[1]"
    assert claim.locator == "/specification/claims/claim[1]"
    with pytest.raises(ValueError, match="DOCTYPE"):
        parse_specification(SPEC, "000000001", grant_number="I000001")


@pytest.mark.parametrize("dtd_version", [b"1.0.0", b"2.0.1"])
def test_utility_model_uses_a_verified_model_dtd_version(dtd_version):
    model = SPEC.replace(b"invention-specification", b"specification").replace(
        b"A103.1.0", dtd_version
    )
    [section], [claim] = parse_specification(model, "000000001", grant_number="M000001")
    assert section.locator.endswith("/technical-field/p[1]")
    assert claim.number == 1
    with pytest.raises(ValueError, match="Unexpected specification format"):
        parse_specification(model, "000000001", grant_number="I000001")
    abstracts = b'<abstract lang="tw"><abstract-dtext>DEMO <b>TW</b></abstract-dtext></abstract><abstract lang="en"><abstract-dtext>DEMO EN</abstract-dtext></abstract>'
    model = model.replace(b"<description>", abstracts + b"<description>")
    _, chinese, english = parse_specification(
        model, "000000001", grant_number="M000001"
    )[0]
    assert (chinese.kind, chinese.text, chinese.locator) == (
        "abstract-zh",
        "DEMO TW",
        "/specification/abstract[1]/abstract-dtext[1]",
    )
    assert (english.kind, english.text, english.locator) == (
        "abstract-en",
        "DEMO EN",
        "/specification/abstract[2]/abstract-dtext[1]",
    )


def test_design_specification_keeps_description_without_claims():
    design = (
        SPEC.replace(b"invention-specification", b"specification")
        .replace(b"A103.1.0", b"2.0.1")
        .replace(b"technical-field", b"main-use")
    )
    with pytest.raises(ValueError, match="Unexpected claims"):
        parse_specification(design, "000000001", grant_number="D000001")
    design = design.split(b"<claims>")[0] + b"</specification>"
    [section], claims = parse_specification(design, "000000001", grant_number="D000001")
    assert section.locator == "/specification/description/main-use/p[1]"
    assert claims == []


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
