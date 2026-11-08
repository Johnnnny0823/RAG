import hashlib

import pytest

from services.ingestion.artifacts import LocalObjectStore, RawArtifact


def test_object_store_deduplicates_and_detects_corruption(tmp_path):
    store = LocalObjectStore(tmp_path)
    payload = b"<DEMO/>"
    artifact = store.put(payload)
    assert store.put(payload) == artifact
    assert artifact.checksum == hashlib.sha256(payload).hexdigest()
    assert store.read(artifact) == payload

    (tmp_path / artifact.object_key).write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="checksum or size mismatch"):
        store.put(payload)


def test_object_store_rejects_untrusted_locator(tmp_path):
    store = LocalObjectStore(tmp_path)
    with pytest.raises(ValueError, match="Invalid artifact locator"):
        store.read(RawArtifact("a" * 64, "../outside", 0))
