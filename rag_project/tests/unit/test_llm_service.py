import httpx
import pytest

from rag_project.rag_core.infra.llm_ollama import OllamaLLMProvider


class _DummyResponse:
    def __init__(self, data):
        self._data = data
        self.status_code = 200

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=None)

    def json(self):
        return self._data


def test_llm_service_builds_prompt_and_returns_response(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return _DummyResponse({"response": "hello"})

    monkeypatch.setattr("httpx.post", fake_post)
    provider = OllamaLLMProvider(base_url="http://ollama.test", model="primary", fallback_model="secondary", timeout=1.0)

    out = provider.generate("question here", max_tokens=16)

    assert out == "hello"
    assert captured["json"]["model"] == "primary"
    assert captured["json"]["options"]["num_predict"] == 16


def test_llm_service_uses_fallback_on_http_error(monkeypatch):
    calls = {"count": 0, "models": []}

    def fake_post(_url, json, timeout):
        calls["count"] += 1
        calls["models"].append(json["model"])
        if calls["count"] == 1:
            raise httpx.HTTPError("fail")
        return _DummyResponse({"response": "fallback text"})

    monkeypatch.setattr("httpx.post", fake_post)
    provider = OllamaLLMProvider(base_url="http://ollama.test", model="primary", fallback_model="secondary", timeout=1.0)

    out = provider.generate("prompt")

    assert calls["models"] == ["primary", "secondary"]
    assert out == "fallback text"


def test_llm_service_raises_when_unreachable(monkeypatch):
    monkeypatch.setattr("httpx.post", lambda *_args, **_kwargs: (_ for _ in ()).throw(httpx.TimeoutException("timeout")))
    provider = OllamaLLMProvider(base_url="http://ollama.test", model="primary", fallback_model="primary", timeout=0.1)

    with pytest.raises(httpx.HTTPError):
        provider.generate("prompt", max_tokens=4)


def test_llm_service_handles_empty_prompt(monkeypatch):
    monkeypatch.setattr("httpx.post", lambda *_a, **_k: _DummyResponse({"response": "ok"}))
    provider = OllamaLLMProvider(base_url="http://ollama.test", model="primary")

    out = provider.generate("", max_tokens=2)

    assert out == "ok"
