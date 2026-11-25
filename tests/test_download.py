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
