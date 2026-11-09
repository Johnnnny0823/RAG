"""Shared transport for explicitly configured local Ollama models."""

import json
import os
import re
from dataclasses import dataclass
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class LocalModelError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class LocalOllamaModel:
    url: str
    name: str
    digest: str

    @classmethod
    def from_env(cls, prefix):
        url = os.getenv(f"{prefix}_URL", "").rstrip("/")
        name = os.getenv(f"{prefix}_MODEL", "")
        digest = os.getenv(f"{prefix}_DIGEST", "")
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
            raise LocalModelError(
                "A local Ollama URL, explicit model tag and SHA-256 digest are required"
            )
        return cls(url, name, digest)

    def request_json(self, path, payload=None, *, timeout=90):
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(
            self.url + path, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            opener = build_opener(ProxyHandler({}), NoRedirect())
            with opener.open(request, timeout=timeout) as response:
                return json.loads(response.read(8 * 1024 * 1024))
        except (URLError, OSError, ValueError) as exc:
            raise LocalModelError("Local Ollama request failed") from exc

    def verify_digest(self):
        response = self.request_json("/api/tags")
        models = response.get("models", []) if isinstance(response, dict) else []
        if not isinstance(models, list) or not any(
            isinstance(model, dict)
            and model.get("name") == self.name
            and model.get("digest") == self.digest
            for model in models
        ):
            raise LocalModelError("Local Ollama model digest does not match")
