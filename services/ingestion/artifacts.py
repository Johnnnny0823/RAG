"""Store and verify immutable source bytes by SHA-256."""

import argparse
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

MAX_XML_BYTES = 16 * 1024 * 1024
MAX_GAZETTE_XML_BYTES = 32 * 1024 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}")


def add_objects_argument(parser: argparse.ArgumentParser) -> None:
    default = os.environ.get("PATENT_OBJECTS_DIR")
    parser.add_argument(
        "--objects",
        type=Path,
        default=default,
        required=not default,
        help="Raw object directory (defaults to PATENT_OBJECTS_DIR when configured)",
    )


@dataclass(frozen=True)
class RawArtifact:
    checksum: str
    object_key: str
    size_bytes: int


class LocalObjectStore:
    def __init__(self, root: Path):
        self.root = root

    def put(self, data: bytes) -> RawArtifact:
        if len(data) > MAX_GAZETTE_XML_BYTES:
            raise ValueError("XML artifact exceeds the size limit")
        checksum = hashlib.sha256(data).hexdigest()
        artifact = RawArtifact(checksum, f"sha256/{checksum[:2]}/{checksum}", len(data))
        path = self.root / artifact.object_key
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            with NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(data)
            try:
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
        self.read(artifact)
        return artifact

    def read(self, artifact: RawArtifact) -> bytes:
        checksum = artifact.checksum
        if not SHA256.fullmatch(checksum) or artifact.object_key != (
            f"sha256/{checksum[:2]}/{checksum}"
        ):
            raise ValueError("Invalid artifact locator")
        with (self.root / artifact.object_key).open("rb") as stream:
            data = stream.read(MAX_GAZETTE_XML_BYTES + 1)
        if (
            len(data) > MAX_GAZETTE_XML_BYTES
            or len(data) != artifact.size_bytes
            or hashlib.sha256(data).hexdigest() != checksum
        ):
            raise ValueError("Artifact checksum or size mismatch")
        return data
