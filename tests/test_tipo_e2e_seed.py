import hashlib

import pytest

from scripts.seed_tipo_e2e import prepare


def test_seed_rejects_mismatched_cache_without_overwriting(tmp_path):
    cache = tmp_path / "spec.xml"
    cache.write_bytes(b"unexpected bytes")
    expected = hashlib.sha256(b"expected bytes").hexdigest()

    with pytest.raises(ValueError, match="unexpected SHA-256"):
        prepare(cache, "unused", expected, offline=True)

    assert cache.read_bytes() == b"unexpected bytes"
