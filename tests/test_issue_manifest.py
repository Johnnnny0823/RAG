from ftplib import error_temp

import pytest

from services.ingestion.issue_manifest import fetch_specifications, resolve_spec_urls

URL = "ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/index_all.xml"
PUBLICATION = "000000002"
APPLICATION = "000000001"
PATH = "/InventionPubXML_024019/2419000000002/000000001-A0304.xml"


def manifest(path=PATH):
    return f"""<tw-patent-applications total-count="1">
        <tw-patent-application publication-number="{PUBLICATION}">
            <specification-files xml-file="{path}"/>
        </tw-patent-application>
    </tw-patent-applications>""".encode()


def test_manifest_binds_issue_publication_and_application():
    assert resolve_spec_urls(manifest(), URL, "024019", {PUBLICATION: APPLICATION}) == {
        PUBLICATION: f"ftps://ftp.tipo.gov.tw/InventionPubXML/115{PATH}"
    }
    with pytest.raises(ValueError, match="requested TIPO issue"):
        resolve_spec_urls(manifest(), URL, "024020", {PUBLICATION: APPLICATION})
    with pytest.raises(ValueError, match="Invalid or duplicate"):
        resolve_spec_urls(manifest(), URL, "024019", {PUBLICATION: "000000003"})
    with pytest.raises(ValueError, match="Invalid or duplicate"):
        resolve_spec_urls(
            manifest(PATH.replace("/2419", "/../2419")),
            URL,
            "024019",
            {PUBLICATION: APPLICATION},
        )


def test_success_is_cached_and_failure_is_retried(tmp_path, monkeypatch):
    calls = []
    urls = {"good": "good-url", "retry": "retry-url"}

    def download(url):
        calls.append(url)
        if url == "retry-url" and calls.count(url) == 1:
            raise error_temp("426 fixture transfer aborted")
        return b"<DEMO/>"

    monkeypatch.setattr("services.ingestion.issue_manifest.download_ftps_xml", download)
    monkeypatch.setattr("services.ingestion.issue_manifest.time.sleep", lambda _: None)
    cached, failed = fetch_specifications(urls, tmp_path)
    assert cached["good"].read_bytes() == b"<DEMO/>"
    assert "426" in failed["retry"]
    cached, failed = fetch_specifications(urls, tmp_path)
    assert not failed
    assert set(cached) == set(urls)
    assert calls == ["good-url", "retry-url", "retry-url"]
    cached, failed = fetch_specifications(
        {**urls, "absent": "absent-url"}, tmp_path, cache_only=True
    )
    assert set(cached) == set(urls)
    assert "No cached TIPO XML" in failed["absent"]
    assert "absent-url" not in calls
