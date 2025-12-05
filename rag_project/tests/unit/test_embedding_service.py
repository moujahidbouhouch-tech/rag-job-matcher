import math
from typing import List

import pytest

from rag_project.rag_core.ingestion.chunker import chunk_text
from rag_project.rag_core.infra.embedding_bgem3 import BgeM3EmbeddingProvider


class _FakeVector:
    def __init__(self, data: List[float]) -> None:
        self._data = data

    def tolist(self) -> List[float]:
        return list(self._data)


class _FakeSentenceTransformer:
    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def encode(self, texts, normalize_embeddings=True):
        # Deterministic encoding: vector based on char codes of the text
        def _encode_one(t: str) -> List[float]:
            raw = [float((ord(c) % 32) / 100.0) for c in t]
            if not raw:
                raw = [0.0]
            if normalize_embeddings:
                norm = math.sqrt(sum(x * x for x in raw)) or 1.0
                raw = [x / norm for x in raw]
            return raw

        if isinstance(texts, str):
            return _FakeVector(_encode_one(texts))
        return [_FakeVector(_encode_one(t)) for t in texts]


@pytest.fixture(autouse=True)
def fake_model(monkeypatch):
    monkeypatch.setattr(
        "rag_project.rag_core.infra.embedding_bgem3.SentenceTransformer",
        _FakeSentenceTransformer,
    )
    yield


def test_embedding_service_deterministic_outputs():
    provider = BgeM3EmbeddingProvider("fake-model")
    vec1 = provider.embed(["hello"])[0]
    vec2 = provider.embed(["hello"])[0]
    assert vec1 == vec2


def test_embedding_service_differs_for_different_texts():
    provider = BgeM3EmbeddingProvider("fake-model")
    a, b = provider.embed(["alpha"]), provider.embed(["beta"])
    assert a[0] != b[0]


def test_embedding_service_batch_equals_single():
    provider = BgeM3EmbeddingProvider("fake-model")
    single = provider.embed(["sample"])[0]
    batch_first, batch_second = provider.embed(["sample", "sample"])
    assert single == batch_first == batch_second


def test_embedding_service_handles_empty_and_long_input():
    provider = BgeM3EmbeddingProvider("fake-model")
    empty_vec = provider.embed(["   "])[0]
    assert all(isinstance(x, float) for x in empty_vec)
    long_text = "x" * 10000
    long_vec = provider.embed([long_text])[0]
    assert len(long_vec) >= 1


def test_embedding_service_handles_unicode_characters():
    provider = BgeM3EmbeddingProvider("fake-model")
    vec = provider.embed(["こんにちは 😊"])
    assert len(vec[0]) >= 1


def test_embedding_service_integration_parse_chunk_embed():
    text = "Sentence one ends here. Sentence two follows soon."
    chunks = chunk_text(text, max_tokens=5, overlap_tokens=2)
    provider = BgeM3EmbeddingProvider("fake-model")
    vectors = provider.embed(chunks)
    assert len(vectors) == len(chunks)
    assert all(isinstance(v, list) for v in vectors)
