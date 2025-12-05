import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from dotenv import load_dotenv

from rag_project.config import (
    MODELS,
    BOUNDARY_PATTERN_WEIGHTS,
    CHUNK_ASSIST_MAX_OUTPUT_TOKENS,
    CHUNK_BOUNDARY_PATTERNS,
    CHUNK_OVERLAP_TOKENS,
    CHUNK_TOKEN_TARGET,
    DB_DEFAULT_HOST,
    DB_DEFAULT_NAME,
    DB_DEFAULT_PASSWORD,
    DB_DEFAULT_PORT,
    DB_DEFAULT_USER,
    TEST_DB_HOST,
    TEST_DB_NAME,
    TEST_DB_PASSWORD,
    TEST_DB_PORT,
    TEST_DB_USER,
    CHUNK_ASSIST_MODEL_ID,
    CHUNK_PROFILES,
    EMBEDDING_DIM,
    EMBEDDING_MODEL_ID,
    OLLAMA_DEFAULT_FALLBACK_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
    OLLAMA_DEFAULT_HOST,
    OLLAMA_DEFAULT_MODEL,
    STRUCTURED_MAX_LLM_INPUT_WORDS,
    STRUCTURED_MIN_CHUNK_WORDS,
)

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=False)


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(name, default)


def _env_first(names: list[str], default: Optional[str] = None) -> Optional[str]:
    for n in names:
        val = os.getenv(n)
        if val is not None:
            return val
    return default


@dataclass
class AppSettings:
    # Database
    db_host: str = _env_first(
        ["POSTGRES_HOST_RAG", "POSTGRES_HOST", "DB_POSTGRESDB_HOST", "DB_HOST"],
        DB_DEFAULT_HOST,
    )
    db_port: int = int(
        _env_first(
            ["POSTGRES_PORT_RAG", "POSTGRES_PORT", "DB_POSTGRESDB_PORT", "DB_PORT"],
            str(DB_DEFAULT_PORT),
        )
    )
    db_name: str = _env_first(
        ["POSTGRES_DB_RAG", "POSTGRES_DB", "DB_POSTGRESDB_DATABASE", "DB_NAME"],
        DB_DEFAULT_NAME,
    )
    db_user: str = _env_first(
        ["POSTGRES_USER_RAG", "POSTGRES_USER", "DB_POSTGRESDB_USER", "DB_USER"],
        DB_DEFAULT_USER,
    )
    db_password: Optional[str] = _env_first(
        ["POSTGRES_PASSWORD_RAG", "POSTGRES_PASSWORD", "DB_POSTGRESDB_PASSWORD", "DB_PASSWORD"],
        DB_DEFAULT_PASSWORD,
    )

    # Ollama
    ollama_host: str = _env("OLLAMA_HOST", OLLAMA_DEFAULT_HOST)
    ollama_model: str = _env("OLLAMA_MODEL", OLLAMA_DEFAULT_MODEL)
    ollama_fallback_model: str = _env("OLLAMA_FALLBACK_MODEL", OLLAMA_DEFAULT_FALLBACK_MODEL)
    ollama_num_ctx: int = int(_env("OLLAMA_NUM_CTX", str(MODELS["llm_primary"]["ollama_num_ctx"])))

    # timeout
    ollama_timeout: float = float(_env("OLLAMA_TIMEOUT", str(OLLAMA_TIMEOUT_SECONDS)))
    # Embeddings
    embedding_model_id: str = _env("EMBEDDING_MODEL_ID", EMBEDDING_MODEL_ID)
    embedding_dim: int = int(_env("EMBEDDING_DIM", str(EMBEDDING_DIM)))

    # Chunking
    chunk_token_target: int = int(_env_first(["CHUNK_TOKEN_TARGET"], str(CHUNK_TOKEN_TARGET)))
    chunk_overlap_tokens: int = int(_env_first(["CHUNK_OVERLAP_TOKENS"], str(CHUNK_OVERLAP_TOKENS)))
    use_structured_chunker: bool = _env("USE_STRUCTURED_CHUNKER", "true").lower() in {"1", "true", "yes"}
    structured_min_chunk_words: int = int(_env("STRUCTURED_MIN_CHUNK_WORDS", str(STRUCTURED_MIN_CHUNK_WORDS)))
    structured_max_llm_input_words: int = int(_env("STRUCTURED_MAX_LLM_INPUT_WORDS", str(STRUCTURED_MAX_LLM_INPUT_WORDS)))
    structured_use_llm: bool = _env("STRUCTURED_USE_LLM", "0").lower() in {"1", "true", "yes"}
    chunk_assist_model_id: str = _env("CHUNK_ASSIST_MODEL_ID", CHUNK_ASSIST_MODEL_ID)
    chunk_profiles: dict = field(default_factory=lambda: CHUNK_PROFILES.copy())

    def __post_init__(self):
        # Ensure ollama_host has scheme
        parsed = urlparse(self.ollama_host)
        if not parsed.scheme:
            self.ollama_host = f"http://{self.ollama_host}"
        if self.db_host == "postgres":
            self.db_host = "localhost"
        # Force test DB when running under pytest to avoid touching real data.
        if os.getenv("PYTEST_CURRENT_TEST"):
            self.db_host = os.getenv("TEST_DB_HOST", TEST_DB_HOST)
            self.db_port = int(os.getenv("TEST_DB_PORT", TEST_DB_PORT))
            self.db_name = os.getenv("TEST_DB_NAME", TEST_DB_NAME)
            self.db_user = os.getenv("TEST_DB_USER", TEST_DB_USER)
            self.db_password = os.getenv("TEST_DB_PASSWORD", TEST_DB_PASSWORD)


@lru_cache()
def get_settings() -> AppSettings:
    return AppSettings()


def _mask(value: Optional[str]) -> str:
    if value is None or value == "":
        return ""
    return "***"


if __name__ == "__main__":
    settings = get_settings()
    print("RAG Settings (env precedence applied)")
    print(f"db_host={settings.db_host}")
    print(f"db_port={settings.db_port}")
    print(f"db_name={settings.db_name}")
    print(f"db_user={settings.db_user}")
    print(f"db_password={_mask(settings.db_password)}")
    print(f"ollama_host={settings.ollama_host}")
    print(f"ollama_model={settings.ollama_model}")
    print(f"ollama_fallback_model={settings.ollama_fallback_model}")
    print(f"embedding_model_id={settings.embedding_model_id}")
    print(f"chunk_token_target={settings.chunk_token_target}")
    print(f"chunk_overlap_tokens={settings.chunk_overlap_tokens}")
    print(f"use_structured_chunker={settings.use_structured_chunker}")
    print(f"structured_min_chunk_words={settings.structured_min_chunk_words}")
    print(f"structured_max_llm_input_words={settings.structured_max_llm_input_words}")
    print(f"structured_use_llm={settings.structured_use_llm}")
    print(f"chunk_assist_model_id={settings.chunk_assist_model_id}")
