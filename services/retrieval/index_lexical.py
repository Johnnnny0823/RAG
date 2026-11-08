"""Index missing document versions from PostgreSQL in bounded transactions."""

import argparse

from services.api.db import engine
from services.retrieval.lexical import TOKENIZER_VERSION, tokenize

# An empty marker is inserted with every document's chunks in the same transaction.
# It also marks documents that have no tokenizable text.
CANDIDATES = """
    SELECT d.id FROM patent_documents d
    WHERE d.jurisdiction = 'TW'
      AND EXISTS (
        SELECT 1 FROM document_artifacts da
        JOIN ingestion_artifacts ia ON ia.id = da.artifact_id
        JOIN ingestion_batches b ON b.id = ia.batch_id
        JOIN source_datasets s ON s.id = b.dataset_id
        WHERE da.document_id = d.id AND NOT s.is_demo
          AND ia.status IN ('parsed', 'partial') AND b.status IN ('complete', 'partial')
      )
      AND NOT EXISTS (
        SELECT 1 FROM patent_lexical_chunks t
        WHERE t.document_id = d.id AND t.tokenizer_version = %s
          AND t.field = 'indexed' AND t.ordinal = 0
      )
    ORDER BY d.id LIMIT %s
"""

CHUNKS = """
    SELECT d.id, fields.field, 0 AS ordinal, fields.body
    FROM patent_documents d CROSS JOIN LATERAL (
        VALUES ('title_zh', d.title_zh), ('title_en', d.title_en),
               ('abstract_zh', d.abstract_zh), ('abstract_en', d.abstract_en)
    ) AS fields(field, body)
    WHERE d.id = ANY(%s::uuid[]) AND fields.body IS NOT NULL
    UNION ALL
    SELECT document_id, 'claim', claim_number, text FROM patent_claims
    WHERE document_id = ANY(%s::uuid[])
    UNION ALL
    SELECT document_id, 'section:' || section_type, ordinal, original_text
    FROM patent_sections WHERE document_id = ANY(%s::uuid[])
"""

INSERT = """
    INSERT INTO patent_lexical_chunks (document_id, tokenizer_version, field, ordinal, tokens)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT DO NOTHING
"""


def index_missing(batch_size: int) -> tuple[int, int]:
    document_count = chunk_count = 0
    while True:
        with engine.begin() as conn:
            document_ids = list(
                conn.exec_driver_sql(
                    CANDIDATES, (TOKENIZER_VERSION, batch_size)
                ).scalars()
            )
            if not document_ids:
                return document_count, chunk_count
            chunks = []
            for document_id, field, ordinal, body in conn.exec_driver_sql(
                CHUNKS, (document_ids,) * 3
            ):
                tokens = tokenize(body)
                if tokens:
                    chunks.append(
                        (
                            document_id,
                            TOKENIZER_VERSION,
                            field,
                            ordinal,
                            " ".join(tokens),
                        )
                    )
            markers = [
                (document_id, TOKENIZER_VERSION, "indexed", 0, "")
                for document_id in document_ids
            ]
            conn.exec_driver_sql(INSERT, chunks + markers)
            document_count += len(document_ids)
            chunk_count += len(chunks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 100:
        parser.error("--batch-size must be between 1 and 100")
    documents, chunks = index_missing(args.batch_size)
    print(
        f"Indexed {documents} document versions and {chunks} text chunks ({TOKENIZER_VERSION})"
    )
