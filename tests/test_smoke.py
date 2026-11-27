import io
import json

import pytest

from scripts import smoke


@pytest.mark.parametrize(
    ("total", "lexical", "semantic", "cache_control", "error"),
    [
        (3, 3, 2, "no-store", None),
        (0, 0, 0, "no-store", "no usable lexical or semantic coverage"),
        (3, 3, 0, "no-store", "no usable lexical or semantic coverage"),
        (3, 3, 4, "no-store", "no usable lexical or semantic coverage"),
        (3, 3, 2, "public", "disable response caching"),
    ],
)
def test_official_corpus_preflight(
    monkeypatch, total, lexical, semantic, cache_control, error
):
    response = io.StringIO(
        json.dumps(
            {
                "documents_total": total,
                "lexical_indexed_documents": lexical,
                "semantic_indexed_documents": semantic,
            }
        )
    )
    response.headers = {"Cache-Control": cache_control}
    monkeypatch.setattr(smoke, "urlopen", lambda *_args, **_kwargs: response)

    if error:
        with pytest.raises(ValueError, match=error):
            smoke.verify_official_index("http://127.0.0.1:5173")
    else:
        smoke.verify_official_index("http://127.0.0.1:5173")
