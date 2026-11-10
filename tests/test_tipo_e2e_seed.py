import hashlib
import json

import pytest

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
