import hashlib
import json
from types import SimpleNamespace

import pytest

from scripts import seed_tipo_e2e
from scripts.seed_tipo_e2e import EXPECTED, check_import, prepare


def test_seed_rejects_mismatched_cache_without_overwriting(tmp_path):
    cache = tmp_path / "spec.xml"
    cache.write_bytes(b"unexpected bytes")
    expected = hashlib.sha256(b"expected bytes").hexdigest()

    with pytest.raises(ValueError, match="unexpected SHA-256"):
        prepare(cache, "unused", expected, offline=True)

    assert cache.read_bytes() == b"unexpected bytes"


def test_seed_checks_counts_of_new_and_reused_imports():
    counts = EXPECTED[1]
    reused = {"status": "partial", "reused": True, **counts}
    output = "compose notice\n" + json.dumps(reused)

    assert check_import(output, counts) == reused
    failed_download = {
        **reused,
        "fulltext": 16,
        "download_failures": [{"publication_no": "202640162"}],
    }
    with pytest.raises(ValueError, match="Unexpected import result"):
        check_import(json.dumps(failed_download), counts)


def test_prepare_only_checks_all_official_inputs_without_docker(tmp_path, monkeypatch):
    checked = []

    def check(path, url, checksum, *, offline):
        assert path.is_relative_to(tmp_path)
        assert url.startswith("ftps://ftp.tipo.gov.tw/") and len(checksum) == 64
        assert offline
        checked.append(path)
        return False

    monkeypatch.setattr(seed_tipo_e2e, "prepare", check)
    monkeypatch.setattr(
        seed_tipo_e2e.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("Docker invoked"),
    )
    monkeypatch.setattr(
        "sys.argv", ["seed", str(tmp_path), "--prepare-only", "--offline"]
    )
    seed_tipo_e2e.main()
    assert len(set(checked)) == 24


def test_skip_semantic_keeps_import_verification_and_lexical_index(
    tmp_path, monkeypatch
):
    prepared = []
    commands = []
    outputs = iter(EXPECTED)

    def run(command, **kwargs):
        commands.append(command)
        if kwargs.get("stdout") is not None:
            return SimpleNamespace(stdout=json.dumps(next(outputs)))
        return SimpleNamespace()

    monkeypatch.setattr(
        seed_tipo_e2e,
        "prepare_fixtures",
        lambda path, *, offline: prepared.append((path, offline)),
    )
    monkeypatch.setattr(seed_tipo_e2e.subprocess, "run", run)
    monkeypatch.setattr(
        "sys.argv", ["seed", str(tmp_path), "--skip-semantic", "--offline"]
    )
    seed_tipo_e2e.main()
    assert prepared == [(tmp_path.resolve(), True)]
    assert (
        sum("services.ingestion.import_issue" in command for command in commands) == 3
    )
    assert (
        sum("services.ingestion.verify_document" in command for command in commands)
        == 3
    )
    assert "services.retrieval.index_lexical" in commands[-1]
    assert not any(
        "services.retrieval.index_semantic" in command for command in commands
    )
