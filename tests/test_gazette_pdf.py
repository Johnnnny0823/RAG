from types import SimpleNamespace

import pytest

from services.ingestion import gazette_pdf


def test_gazette_pdf_requires_requested_official_case_and_issue():
    path = "/S220/downloads/invention/pub024019/pdfdata/113133932.pdf"
    case = {
        "applicationNo": "113133932",
        "publicationNo": "202639611",
        "vol": 24,
        "no": 19,
        "pdfUrl": "https://cloud.tipo.gov.tw" + path,
    }
    assert (
        gazette_pdf.checked_pdf_path(
            {"patentDoc": case}, "113133932", "202639611", "024019"
        )
        == path
    )
    for wrong in (
        {"publicationNo": "202639612"},
        {"no": 20},
        {"pdfUrl": "https://example.invalid" + path},
    ):
        with pytest.raises(ValueError, match="identity or PDF location"):
            gazette_pdf.checked_pdf_path(
                {"patentDoc": {**case, **wrong}}, "113133932", "202639611", "024019"
            )


def test_gazette_pdf_identity_comes_from_labeled_numbers(monkeypatch):
    page = SimpleNamespace(
        extract_text=lambda: (
            "【12】發明公開公報（A）公開編號：202639611 其他案號：113133932 申請案號：113133933"
        )
    )
    monkeypatch.setattr(
        gazette_pdf,
        "PdfReader",
        lambda *args, **kwargs: SimpleNamespace(is_encrypted=False, pages=[page]),
    )
    with pytest.raises(ValueError, match="first-page identity"):
        gazette_pdf.verify_pdf(b"%PDF-DEMO", "113133932", "202639611")
    assert gazette_pdf.verify_pdf(b"%PDF-DEMO", "113133933", "202639611") == 1


def test_grant_pdf_keeps_publication_and_certificate_numbers_separate(monkeypatch):
    path = "/S220/downloads/patent/isu053028/pdfdata/114106690.pdf"
    metadata = {
        "patentDoc": {
            "applicationNo": "114106690",
            "publicationNo": "202640162",
            "certificateNo": "I941082",
            "vol": 53,
            "no": 28,
            "pdfUrl": "https://cloud.tipo.gov.tw" + path,
        }
    }
    assert (
        gazette_pdf.checked_pdf_path(
            metadata, "114106690", "I941082", "053028", gazette_pdf.GRANT
        )
        == path
    )
    with pytest.raises(ValueError, match="identity or PDF location"):
        gazette_pdf.checked_pdf_path(metadata, "114106690", "202640162", "053028")
    page = SimpleNamespace(
        extract_text=lambda: (
            "【12】專利公報（B）證書號數：I941082 申請案號：114106690 公開編號：202640162"
        )
    )
    monkeypatch.setattr(
        gazette_pdf,
        "PdfReader",
        lambda *args, **kwargs: SimpleNamespace(is_encrypted=False, pages=[page]),
    )
    assert (
        gazette_pdf.verify_pdf(b"%PDF-DEMO", "114106690", "I941082", gazette_pdf.GRANT)
        == 1
    )
    with pytest.raises(ValueError, match="first-page identity"):
        gazette_pdf.verify_pdf(b"%PDF-DEMO", "114106690", "202640162")
