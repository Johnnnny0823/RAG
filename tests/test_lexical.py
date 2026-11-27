from fastapi.testclient import TestClient

from services.api.main import app
from services.retrieval.lexical import tokenize

client = TestClient(app)


def test_bilingual_tokenizer_preserves_traditional_chinese_and_normalizes_ascii():
    assert tokenize("ＡＩ、動態電阻<br/>ＣＰＵ") == [
        "wai",
        "h0052d500614b",
        "h00614b0096fb",
        "h0096fb00963b",
        "wcpu",
    ]
    assert tokenize("電，阻") == ["h0096fb", "h00963b"]


def test_lexical_endpoint_rejects_unsearchable_query_and_invalid_classifications():
    for payload in [
        {"query": "?! 😅"},
        {"query": "電阻", "ipc": "G01R27"},
        {"query": "電阻", "loc": "13"},
    ]:
        response = client.post("/api/v1/patents/search", json=payload)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "INVALID_REQUEST"
