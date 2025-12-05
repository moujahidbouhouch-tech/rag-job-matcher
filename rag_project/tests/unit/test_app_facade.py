from types import SimpleNamespace

import pytest

from rag_project.config import (
    DB_DEFAULT_HOST,
    DB_DEFAULT_NAME,
    DB_DEFAULT_PASSWORD,
    DB_DEFAULT_PORT,
    DB_DEFAULT_USER,
    CHUNK_ASSIST_MODEL_ID,
    CHUNK_PROFILES,
    EMBEDDING_MODEL_ID,
    LLM_PROVIDER_DEFAULT_MAX_TOKENS,
    MODELS,
    OLLAMA_TIMEOUT_SECONDS,
    OLLAMA_DEFAULT_FALLBACK_MODEL,
    OLLAMA_DEFAULT_HOST,
    OLLAMA_DEFAULT_MODEL,
    STRUCTURED_MAX_LLM_INPUT_WORDS,
    STRUCTURED_MIN_CHUNK_WORDS,
)
from rag_project.rag_core import app_facade


class FakeRepo:
    def __init__(self, dsn):
        self.dsn = dsn


class FakeEmbedder:
    def __init__(self, model_id):
        self.model_id = model_id

    def embed(self, texts):
        return [[0.0] for _ in texts]


class FakeLLM:
    def __init__(self, base_url, model, fallback_model=None, timeout=None, num_ctx=None):
        self.base_url = base_url
        self.model = model
        self.fallback_model = fallback_model

    def generate(self, prompt, model=None, max_tokens=LLM_PROVIDER_DEFAULT_MAX_TOKENS):
        return "ok"


def test_app_facade_wires_dependencies(monkeypatch):
    fake_settings = SimpleNamespace(
        db_host=DB_DEFAULT_HOST,
        db_port=DB_DEFAULT_PORT,
        db_name=DB_DEFAULT_NAME,
        db_user=DB_DEFAULT_USER,
        db_password=DB_DEFAULT_PASSWORD,
        ollama_host=OLLAMA_DEFAULT_HOST,
        ollama_model=OLLAMA_DEFAULT_MODEL,
        ollama_fallback_model=OLLAMA_DEFAULT_FALLBACK_MODEL,
        ollama_timeout=OLLAMA_TIMEOUT_SECONDS,
        ollama_num_ctx=MODELS["llm_primary"]["ollama_num_ctx"],
        embedding_model_id=EMBEDDING_MODEL_ID,
        chunk_token_target=10,
        chunk_overlap_tokens=2,
        use_structured_chunker=False,
        structured_min_chunk_words=STRUCTURED_MIN_CHUNK_WORDS,
        structured_max_llm_input_words=STRUCTURED_MAX_LLM_INPUT_WORDS,
        structured_use_llm=False,
        chunk_assist_model_id=CHUNK_ASSIST_MODEL_ID,
        chunk_profiles=CHUNK_PROFILES,
    )

    monkeypatch.setattr(app_facade, "get_settings", lambda: fake_settings)
    monkeypatch.setattr(app_facade, "PgVectorRepository", FakeRepo)
    monkeypatch.setattr(app_facade, "BgeM3EmbeddingProvider", FakeEmbedder)
    monkeypatch.setattr(app_facade, "OllamaLLMProvider", FakeLLM)

    rag = app_facade.RAGApp()

    assert isinstance(rag.repo, FakeRepo)
    assert isinstance(rag.embedder, FakeEmbedder)
    assert isinstance(rag.llm, FakeLLM)
    assert rag.ingestion.max_tokens == fake_settings.chunk_token_target
    assert rag.ingestion.overlap_tokens == fake_settings.chunk_overlap_tokens
