from contextlib import contextmanager

import pytest

from services.retrieval import index_semantic
from services.retrieval.embeddings import EmbeddingError


@pytest.mark.parametrize(
    "batch_size, request_timeout", [(0, 90), (25, 90), (2, 0), (2, 1801)]
)
def test_index_rejects_unbounded_configuration_before_access(
    batch_size, request_timeout
):
    with pytest.raises(ValueError, match="Batch size"):
        index_semantic.index_missing(
            None, batch_size=batch_size, request_timeout=request_timeout
        )


@pytest.mark.parametrize("fail", [False, True])
def test_index_uses_bounded_requests_and_publishes_only_complete_group(
    monkeypatch, fail
):
    inserted = []
    requests = []

    class Connection:
        reads = 0

        def exec_driver_sql(self, sql, params=None):
            if sql == index_semantic.MISSING:
                self.reads += 1
                return self
            if sql == index_semantic.CHUNKS:
                return [("DEMO-document", "claim", i, "DEMO text") for i in range(3)]
            if sql == index_semantic.INSERT:
                inserted.extend(params)
            if sql == index_semantic.LOCK_MODEL:
                assert params == (1,)
                return self

        def scalar_one(self):
            return True

        def commit(self):
            pass

        def scalars(self):
            return ["DEMO-document"] if self.reads == 1 else []

    connection = Connection()

    @contextmanager
    def connect():
        yield connection

    monkeypatch.setattr(index_semantic.engine, "begin", connect)
    monkeypatch.setattr(index_semantic.engine, "connect", connect)
    monkeypatch.setattr(index_semantic, "model_id", lambda *_: 1)

    class Model:
        identity = ("DEMO", "DEMO", "a" * 64, "DEMO")

        def verify_digest(self):
            pass

        def embed(self, texts, *, timeout):
            requests.append((texts, timeout))
            if fail and len(requests) == 2:
                raise EmbeddingError("DEMO timeout")
            return [[1.0] for _ in texts]

    if fail:
        with pytest.raises(EmbeddingError, match="DEMO timeout"):
            index_semantic.index_missing(Model(), batch_size=2, request_timeout=180)
        assert inserted == []
    else:
        assert index_semantic.index_missing(
            Model(), batch_size=2, request_timeout=180
        ) == (1, 3)
        assert len(inserted) == 3
        assert [row[3] for row in inserted] == [0, 1, 2]
    assert [len(texts) for texts, _ in requests] == [2, 1]
    assert all(timeout == 180 for _, timeout in requests)
