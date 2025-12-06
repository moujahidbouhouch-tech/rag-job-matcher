"""Qwen LLM provider using a generic HTTP endpoint (e.g., DashScope-compatible)."""

from typing import Optional

import httpx

from rag_project.rag_core.ports.llm_port import LLMProvider
from rag_project.logger import get_logger


logger = get_logger(__name__)


class QwenLLMProvider(LLMProvider):
    """
    Minimal Qwen provider that posts to a configurable endpoint.

    Expects an OpenAI/DashScope-like JSON contract:
    {
        "model": "<model_id>",
        "input": { "messages": [ { "role": "user", "content": "<prompt>" } ] },
        "parameters": { "max_tokens": <int> }
    }
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        logger.info(
            "Qwen client initialized base_url=%s model=%s", self.base_url, self.model
        )

    def generate(
        self, prompt: str, model: Optional[str] = None, max_tokens: int = 256
    ) -> str:
        target_model = model or self.model
        payload = {
            "model": target_model,
            "input": {"messages": [{"role": "user", "content": prompt}]},
            "parameters": {"max_tokens": max_tokens},
        }
        try:
            resp = self.client.post(
                "/api/v1/services/aigc/text-generation/generation", json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            logger.debug(
                "Qwen response ok model=%s tokens=%d", target_model, max_tokens
            )
            # Try multiple common response shapes
            if "output" in data and "text" in data["output"]:
                return data["output"]["text"]
            if "choices" in data and data["choices"]:
                return data["choices"][0].get("message", {}).get("content", "")
            return ""
        except httpx.HTTPError as exc:
            logger.error("Qwen generate failed: %s", exc, exc_info=True)
            raise
