"""Embed missing indexed document versions with the configured local model."""

import argparse

from services.api.db import engine
from services.retrieval.embeddings import (
    DIMENSIONS,
    LocalEmbeddingModel,
    model_id,
    vector_literal,
)
from services.retrieval.index_lexical import CHUNKS
from services.retrieval.lexical import TOKENIZER_VERSION

MISSING = """
    SELECT DISTINCT t.document_id FROM patent_lexical_chunks t
    WHERE t.tokenizer_version = %s AND t.field <> 'indexed'
      AND NOT EXISTS (
        SELECT 1 FROM patent_dense_chunks v WHERE v.model_id = %s AND v.document_id = t.document_id
      )
    ORDER BY t.document_id LIMIT 8
"""

INSERT = """
    INSERT INTO patent_dense_chunks
        (model_id, document_id, field, ordinal, char_start, char_end, embedding)
    VALUES (%s, %s, %s, %s, %s, %s, %s::vector)
    ON CONFLICT DO NOTHING
"""

# Positive bigint advisory keys are available to ingestion orchestration.
LOCK_MODEL = "SELECT pg_try_advisory_lock(-%s::bigint)"


class SemanticIndexBusy(RuntimeError):
    pass


def windows(body):
    for start in range(0, len(body), 900):
        end = min(start + 1000, len(body))
        if body[start:end].strip():
            yield start, end, body[start:end]
        if end == len(body):
            break


def index_missing(
    model: LocalEmbeddingModel, *, batch_size: int = 24, request_timeout: int = 90
) -> tuple[int, int]:
    if not 1 <= batch_size <= 24 or not 1 <= request_timeout <= 1800:
        raise ValueError(
            "Batch size must be 1..24 and request timeout must be 1..1800 seconds"
        )
    model.verify_digest()
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """INSERT INTO patent_embedding_models (provider, model_name, digest, pipeline, dimensions)
               VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
            (*model.identity, DIMENSIONS),
        )
        identity = model_id(conn, model)

    # The engine uses NullPool, so leaving this scope closes the session and its lock.
    with engine.connect() as lock:
        if not lock.exec_driver_sql(LOCK_MODEL, (identity,)).scalar_one():
            raise SemanticIndexBusy("This embedding model is already being indexed")
        lock.commit()
        return _index_batches(model, identity, batch_size, request_timeout)


def _index_batches(
    model: LocalEmbeddingModel, identity: int, batch_size: int, request_timeout: int
) -> tuple[int, int]:
    documents = vectors = 0
    while True:
        with engine.connect() as conn:
            document_ids = list(
                conn.exec_driver_sql(MISSING, (TOKENIZER_VERSION, identity)).scalars()
            )
            if not document_ids:
                return documents, vectors
            chunks = [
                (document_id, field, ordinal, start, end, text)
                for document_id, field, ordinal, body in conn.exec_driver_sql(
                    CHUNKS, (document_ids,) * 3
                )
                for start, end, text in windows(body)
            ]
        embeddings = []
        for offset in range(0, len(chunks), batch_size):
            embeddings.extend(
                model.embed(
                    [row[-1] for row in chunks[offset : offset + batch_size]],
                    timeout=request_timeout,
                )
            )
        with engine.begin() as conn:
            conn.exec_driver_sql(
                INSERT,
                [
                    (identity, *row[:-1], vector_literal(vector))
                    for row, vector in zip(chunks, embeddings, strict=True)
                ],
            )
        documents += len(document_ids)
        vectors += len(chunks)
        print(
            f"Indexed {documents} versions and {vectors} vectors in this run",
            flush=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--request-timeout", type=int, default=90)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 24 or not 1 <= args.request_timeout <= 1800:
        parser.error(
            "Batch size must be 1..24 and request timeout must be 1..1800 seconds"
        )
    try:
        documents, vectors = index_missing(
            LocalEmbeddingModel.from_env(),
            batch_size=args.batch_size,
            request_timeout=args.request_timeout,
        )
    except SemanticIndexBusy as error:
        parser.exit(1, f"{error}\n")
    print(f"Semantic index update complete: {documents} versions and {vectors} vectors")
