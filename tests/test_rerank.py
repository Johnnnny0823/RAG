import json

import pytest

from services.retrieval.ollama import LocalModelError, LocalOllamaModel
from services.retrieval.rerank import rerank_order


@pytest.mark.parametrize("order", [[2, 1], [1, 1], [1, 3], [1], ["1", 2]])
def test_reranker_validates_exact_candidate_permutation(monkeypatch, order):
    model = LocalOllamaModel("http://127.0.0.1:11434", "demo:tag", "a" * 64)
    monkeypatch.setattr(LocalOllamaModel, "verify_digest", lambda self: None)

    def response(_model, path, payload, **_kwargs):
        assert path == "/api/chat"
        schema = payload["format"]["properties"]["order"]
        assert schema["items"] == {"type": "integer", "enum": [1, 2]}
        assert schema["minItems"] == schema["maxItems"] == 2
        return {
            "model": model.name,
            "done_reason": "stop",
            "message": {"content": json.dumps({"order": order})},
        }

    monkeypatch.setattr(LocalOllamaModel, "request_json", response)
    candidates = [{"id": 1, "title": "DEMO A"}, {"id": 2, "title": "DEMO B"}]
    if order == [2, 1]:
        assert rerank_order(model, "DEMO query", candidates) == order
    else:
        with pytest.raises(LocalModelError):
            rerank_order(model, "DEMO query", candidates)
