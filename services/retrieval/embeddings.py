"""Local, digest-pinned Ollama embeddings."""

import json
import math
import os
import re
from dataclasses import dataclass
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

DIMENSIONS = 1024
PIPELINE = "patent-dense-v1"
QUERY_INSTRUCTION = "Given a patent research query, retrieve relevant patent passages."


class EmbeddingError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class LocalEmbeddingModel:
    url: str
    name: str
    digest: str

    @classmethod
    def from_env(cls):
        url = os.getenv("EMBEDDING_URL", "").rstrip("/")
        name = os.getenv("EMBEDDING_MODEL", "")
        digest = os.getenv("EMBEDDING_DIGEST", "")
        try:
            parsed = urlsplit(url)
            valid_url = (
                parsed.scheme == "http"
                and parsed.hostname
                in {"localhost", "127.0.0.1", "::1", "host.docker.internal", "ollama"}
                and not (
                    parsed.username
                    or parsed.password
                    or parsed.query
                    or parsed.fragment
                    or parsed.path
                )
                and parsed.port is not None
            )
        except ValueError:
            valid_url = False
        if (
            not valid_url
            or not re.fullmatch(r"[a-zA-Z0-9_./-]+:[a-zA-Z0-9_.-]+", name)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise EmbeddingError(
                "A local Ollama URL, explicit model tag and SHA-256 digest are required"
            )
        return cls(url, name, digest)

    @property
    def identity(self):
        return "ollama", self.name, self.digest, PIPELINE

    def _request(self, path, payload=None):
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(
            self.url + path, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            opener = build_opener(ProxyHandler({}), NoRedirect())
            with opener.open(request, timeout=90) as response:
                return json.loads(response.read(8 * 1024 * 1024))
        except (URLError, OSError, ValueError) as exc:
            raise EmbeddingError("Local Ollama request failed") from exc

    def verify_digest(self):
        response = self._request("/api/tags")
        models = response.get("models", []) if isinstance(response, dict) else []
        if not isinstance(models, list) or not any(
            isinstance(model, dict)
            and model.get("name") == self.name
            and model.get("digest") == self.digest
            for model in models
        ):
            raise EmbeddingError("Local embedding model digest does not match")

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.verify_digest()
        response = self._request(
            "/api/embed",
            {
                "model": self.name,
                "input": texts,
                "truncate": False,
                "options": {"num_ctx": 4096},
            },
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
