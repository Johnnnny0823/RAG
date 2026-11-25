"""Local, digest-pinned Ollama embeddings."""

import json
import math

from services.retrieval.ollama import LocalModelError as EmbeddingError
from services.retrieval.ollama import LocalOllamaModel

DIMENSIONS = 1024
PIPELINE = "patent-dense-v1"
QUERY_INSTRUCTION = "Given a patent research query, retrieve relevant patent passages."


class LocalEmbeddingModel(LocalOllamaModel):
    @classmethod
    def from_env(cls):
        return super().from_env("EMBEDDING")

    @property
    def identity(self):
        return "ollama", self.name, self.digest, PIPELINE

    def embed(self, texts: list[str], *, timeout: int = 90) -> list[list[float]]:
        self.verify_digest()
        response = self.request_json(
            "/api/embed",
            {
                "model": self.name,
                "input": texts,
                "truncate": False,
                "options": {"num_ctx": 4096},
            },
            timeout=timeout,
        )
        self.verify_digest()
        if not isinstance(response, dict) or response.get("model") != self.name:
            raise EmbeddingError("Unexpected embedding model response")
        vectors = response.get("embeddings")
        if not isinstance(vectors, list) or len(vectors) != len(texts):
            raise EmbeddingError("Unexpected number of embeddings")
        for vector in vectors:
            if (
                not isinstance(vector, list)
                or len(vector) != DIMENSIONS
                or any(
                    type(value) not in (int, float)
                    or not math.isfinite(value)
                    or abs(value) > 1.001
                    for value in vector
                )
                or not any(vector)
            ):
                raise EmbeddingError("Invalid embedding vector")
        return vectors

    def embed_query(self, query: str) -> list[float]:
        return self.embed([f"Instruct: {QUERY_INSTRUCTION}\nQuery:{query}"])[0]


def vector_literal(vector: list[float]) -> str:
    return json.dumps(vector, separators=(",", ":"), allow_nan=False)


def model_id(conn, model: LocalEmbeddingModel) -> int | None:
    return conn.exec_driver_sql(
        """SELECT id FROM patent_embedding_models
           WHERE provider = %s AND model_name = %s AND digest = %s AND pipeline = %s""",
        model.identity,
    ).scalar_one_or_none()
