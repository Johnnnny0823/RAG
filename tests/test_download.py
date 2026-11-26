from ftplib import error_perm, error_temp
from unittest.mock import Mock, call

import pytest

from services.ingestion import download

OFFICIAL_PATH = "/InventionPubXML/115/InventionPubXML_024019/index.xml"
OFFICIAL_URL = f"ftps://ftp.tipo.gov.tw{OFFICIAL_PATH}"


@pytest.mark.parametrize(
    ("attempts", "delays", "expected_error"),
    [
        ([error_temp("425 Listener busy"), b"<index/>"], [15], None),
        ([error_temp("425 Listener busy")] * 3, [15, 45], error_temp),
        ([error_perm("550 Not found")], [], error_perm),
        ([ValueError("Incomplete transfer")], [], ValueError),
    ],
)
def test_tipo_download_retries_only_425(monkeypatch, attempts, delays, expected_error):
    context = object()
    transfer = Mock(side_effect=attempts)
    wait = Mock()
    monkeypatch.setattr(download, "tls_context", lambda: context)
    monkeypatch.setattr(download, "_transfer_xml", transfer)
    monkeypatch.setattr(download, "sleep", wait)

    if expected_error:
        with pytest.raises(expected_error):
            download.download_ftps_xml(OFFICIAL_URL)
    else:
        assert download.download_ftps_xml(OFFICIAL_URL) == b"<index/>"

    assert transfer.call_args_list == [
        call(OFFICIAL_PATH, context, download.MAX_XML_BYTES)
    ] * len(attempts)
    assert wait.call_args_list == [call(seconds) for seconds in delays]


def test_only_grant_archive_index_uses_the_larger_gazette_limit(monkeypatch):
    context = object()
    transfer = Mock(return_value=b"<index/>")
    monkeypatch.setattr(download, "tls_context", lambda: context)
    monkeypatch.setattr(download, "_transfer_xml", transfer)
    folder = "/PatentIsuRegSpecXMLA/114/PatentIsuRegSpecXMLA_052006"
    index = folder + "/index.xml"
    individual = folder + "/example.xml"

    for path in (index, individual):
        download.download_ftps_xml(f"ftps://ftp.tipo.gov.tw{path}")

    assert transfer.call_args_list == [
        call(index, context, download.MAX_GAZETTE_XML_BYTES),
        call(individual, context, download.MAX_XML_BYTES),
    ]


def test_archived_index_cli_can_save_a_large_grant_index(tmp_path, monkeypatch):
    target = tmp_path / "grant-index.xml"
    url = "ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/114/PatentIsuRegSpecXMLA_052006/index.xml"
    payload = b" " * (download.MAX_XML_BYTES + 1)
    transfer = Mock(return_value=payload)
    monkeypatch.setattr(download, "download_ftps_xml", transfer)
    monkeypatch.setattr(
        "sys.argv", ["download", "--index-out", str(target), "--index-url", url]
    )

    download.main()

    transfer.assert_called_once_with(url)
    assert target.stat().st_size == len(payload)
