import hashlib

import pytest

from services.ingestion.artifacts import LocalObjectStore, RawArtifact
from services.ingestion.sync_objects import verify_objects


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


def test_copy_checks_source_and_preserves_existing_destination(tmp_path):
    original = LocalObjectStore(tmp_path / "original")
    backup = LocalObjectStore(tmp_path / "backup")
    artifact = original.put(b"<DEMO/>")
    assert verify_objects([artifact], original, backup) == 1
    assert verify_objects([artifact], backup) == 1

    (original.root / artifact.object_key).write_bytes(b"corrupt")
    with pytest.raises(ValueError, match=artifact.checksum):
        verify_objects([artifact], original, backup)
    assert backup.read(artifact) == b"<DEMO/>"


def test_backup_can_read_missing_objects_from_a_legacy_store(tmp_path):
    primary = LocalObjectStore(tmp_path / "primary")
    legacy = LocalObjectStore(tmp_path / "legacy")
    backup = LocalObjectStore(tmp_path / "backup")
    pdf = primary.put(b"DEMO PDF bytes")
    xml = legacy.put(b"DEMO XML bytes")
    assert verify_objects([pdf, xml], primary, backup, fallbacks=[legacy]) == 2
    assert verify_objects([pdf, xml], backup) == 2

    damaged = primary.root / xml.object_key
    damaged.parent.mkdir(parents=True)
    damaged.write_bytes(b"damaged primary object")
    with pytest.raises(ValueError, match=xml.checksum):
        verify_objects([xml], primary, backup, fallbacks=[legacy])
