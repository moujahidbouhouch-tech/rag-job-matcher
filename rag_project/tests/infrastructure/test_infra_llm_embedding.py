import os

import httpx
import pytest

from rag_project.infrastructure.health import ollama_base_url

# These tests exercise external services; skip by default unless explicitly enabled.
if os.getenv("RUN_LLM_INFRA_TESTS", "0") != "1":
    pytest.skip("LLM infra tests disabled; set RUN_LLM_INFRA_TESTS=1 to enable.", allow_module_level=True)


def test_ollama_generate_smoke():
    """Call Ollama generate with a tiny prompt to ensure inference is reachable."""
    base_url = ollama_base_url()
    payload = {
        "model": "llama3.1:8b-instruct-q8_0",
        "prompt": "Hi",
        "stream": False,
        "options": {"num_predict": 8},
    }
    try:
        resp = httpx.post(f"{base_url}/api/generate", json=payload, timeout=5.0)
        resp.raise_for_status()
    except (httpx.HTTPError, httpx.RequestError, PermissionError) as exc:
        pytest.skip(
            f"Ollama generate not reachable: {exc}. "
            "Ensure Ollama is running with the required model, then re-run tests."
        )

    data = resp.json()
    assert data.get("model") == payload["model"], "Unexpected model in Ollama response"
    assert data.get("response"), "Empty response from Ollama"


def test_embedding_round_trip():
    """Embed a string twice and verify shape and consistency."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        pytest.skip(f"sentence-transformers not available: {exc}")

    try:
        model = SentenceTransformer("BAAI/bge-m3")
        text = "RAG embedding probe"
        vec1 = model.encode(text, normalize_embeddings=True)
        vec2 = model.encode(text, normalize_embeddings=True)
    except Exception as exc:  # noqa: BLE001 - best-effort infra probe
        pytest.skip(f"Embedding model not available or failed to load: {exc}")

    assert vec1.shape == vec2.shape == (1024,), "Embedding dimension mismatch"
    cosine_sim = float((vec1 @ vec2) / ((vec1**2).sum() ** 0.5 * (vec2**2).sum() ** 0.5))
    assert cosine_sim > 0.999, f"Embedding inconsistency too high (cosine={cosine_sim:.6f})"
