import hashlib
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from services.ingestion import gazette_pdf


def test_temporary_tipo_server_error_is_retried(monkeypatch):
    pending = Mock(status=503)
    ready = Mock(status=200)
    ready.headers.get_content_type.return_value = "application/json"
    ready.read.return_value = b"{}"
    connection = Mock()
    connection.getresponse.side_effect = [pending, ready]
    monkeypatch.setattr(gazette_pdf, "HTTPSConnection", Mock(return_value=connection))
    delay = Mock()
    monkeypatch.setattr(gazette_pdf.time, "sleep", delay)
    assert gazette_pdf.fetch("/gazette", "application/json", 1024) == b"{}"
    assert connection.request.call_count == 2
    delay.assert_called_once_with(1)


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
    assert gazette_pdf.verify_pdf(b"%PDF-DEMO", "113133933", "202639611") == [
        page.extract_text()
    ]


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
    assert gazette_pdf.verify_pdf(
        b"%PDF-DEMO", "114106690", "I941082", gazette_pdf.GRANT
    ) == [page.extract_text()]
    with pytest.raises(ValueError, match="first-page identity"):
        gazette_pdf.verify_pdf(b"%PDF-DEMO", "114106690", "202640162")


def test_expected_digest_rejects_changed_pdf_before_parsing(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "gazette_pdf",
            "--application",
            "114106690",
            "--grant",
            "I941082",
            "--issue",
            "053028",
            "--objects",
            str(tmp_path),
            "--expected-sha256",
            "0" * 64,
        ],
    )
    responses = iter((b"{}", b"%PDF-DEMO"))
    monkeypatch.setattr(gazette_pdf, "fetch", lambda *_: next(responses))
    monkeypatch.setattr(gazette_pdf, "checked_pdf_path", lambda *_: "/demo.pdf")
    monkeypatch.setattr(
        gazette_pdf, "verify_pdf", lambda *_: pytest.fail("Parsed changed PDF")
    )
    with pytest.raises(SystemExit) as error:
        gazette_pdf.main()
    assert error.value.code == 1
    assert "does not match its expected SHA-256" in capsys.readouterr().err


def test_wrong_attachment_is_rejected_before_network_io(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "gazette_pdf",
            "--application",
            "114106690",
            "--grant",
            "I941082",
            "--issue",
            "053028",
            "--objects",
            str(tmp_path),
            "--apply-to",
            "00000000-0000-0000-0000-000000000001",
        ],
    )
    database = MagicMock()
    connection = database.connect.return_value.__enter__.return_value
    connection.exec_driver_sql.return_value.scalar_one_or_none.return_value = None
    monkeypatch.setattr(gazette_pdf, "engine", database)
    monkeypatch.setattr(gazette_pdf, "fetch", lambda *_: pytest.fail("Contacted TIPO"))
    with pytest.raises(SystemExit) as error:
        gazette_pdf.main()
    assert error.value.code == 1
    assert "No matching official document version" in capsys.readouterr().err


def test_archive_preview_validates_case_and_digest_without_fetching(
    monkeypatch, tmp_path, capsys
):
    application = "114106690"
    certificate = "I941082"
    issue = "053028"
    path = gazette_pdf.pdf_path(application, issue, gazette_pdf.GRANT)
    url = "https://cloud.tipo.gov.tw" + path
    case_file = tmp_path / "case.json"
    pdf_file = tmp_path / "gazette.pdf"
    case = {
        "applicationNo": application,
        "certificateNo": certificate,
        "vol": 53,
        "no": 28,
        "pdfUrl": url,
    }
    case_file.write_text(json.dumps({"patentDoc": case}), encoding="utf-8")
    pdf = b"%PDF-DEMO"
    pdf_file.write_bytes(pdf)
    digest = hashlib.sha256(pdf).hexdigest()
    monkeypatch.setattr(
        "sys.argv",
        [
            "gazette_pdf",
            "--application",
            application,
            "--grant",
            certificate,
            "--issue",
            issue,
            "--objects",
            str(tmp_path),
            "--archive-case",
            str(case_file),
            "--archive-pdf",
            str(pdf_file),
            "--expected-sha256",
            digest,
        ],
    )
    monkeypatch.setattr(gazette_pdf, "fetch", lambda *_: pytest.fail("Contacted TIPO"))
    verify_pdf = Mock(return_value=["DEMO"])
    monkeypatch.setattr(gazette_pdf, "verify_pdf", verify_pdf)
    gazette_pdf.main()
    verify_pdf.assert_called_once_with(pdf, application, certificate, gazette_pdf.GRANT)
    assert json.loads(capsys.readouterr().out) == {
        "source_url": url,
        "pages": 1,
        "sha256": digest,
        "attached": False,
    }
    verify_pdf.reset_mock()
    pdf_file.write_bytes(pdf + b"changed")
    with pytest.raises(SystemExit) as error:
        gazette_pdf.main()
    assert error.value.code == 1
    assert "does not match its expected SHA-256" in capsys.readouterr().err
    verify_pdf.assert_not_called()
