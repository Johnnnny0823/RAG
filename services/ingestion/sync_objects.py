"""Verify and optionally copy database-referenced source objects."""

import argparse
from collections.abc import Iterable
from pathlib import Path

from services.api.db import engine
from services.ingestion.artifacts import (
    LocalObjectStore,
    RawArtifact,
    add_objects_argument,
)


def verify_objects(
    artifacts: Iterable[RawArtifact],
    source: LocalObjectStore,
    destination: LocalObjectStore | None = None,
    *,
    fallbacks: Iterable[LocalObjectStore] = (),
) -> int:
    stores = (source, *fallbacks)
    count = 0
    for artifact in artifacts:
        try:
            for store in stores[:-1]:
                try:
                    payload = store.read(artifact)
                except FileNotFoundError:
                    continue
                break
            else:
                payload = stores[-1].read(artifact)
            if destination is not None:
                destination.put(payload)
        except (OSError, ValueError) as error:
            raise ValueError(f"Raw object {artifact.checksum}: {error}") from error
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_objects_argument(parser)
    parser.add_argument("--copy-to", type=Path)
    parser.add_argument(
        "--fallback-objects",
        type=Path,
        action="append",
        default=[],
        help="Read a missing object from this legacy store (repeatable)",
    )
    args = parser.parse_args()
    with engine.connect() as conn:
        artifacts = [
            RawArtifact(*row)
            for row in conn.exec_driver_sql(
                """SELECT DISTINCT checksum, object_key, size_bytes
                   FROM ingestion_artifacts ORDER BY checksum, object_key, size_bytes"""
            )
        ]
    try:
        count = verify_objects(
            artifacts,
            LocalObjectStore(args.objects),
            LocalObjectStore(args.copy_to) if args.copy_to else None,
            fallbacks=[LocalObjectStore(path) for path in args.fallback_objects],
        )
    except ValueError as error:
        parser.exit(1, f"{error}\n")
    print(f"Verified {count} database-referenced raw objects")


if __name__ == "__main__":
    main()
