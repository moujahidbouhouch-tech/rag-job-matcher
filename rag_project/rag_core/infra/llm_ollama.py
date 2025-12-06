from typing import Optional

import httpx

from rag_project.config import (
    LLM_DEFAULT_MAX_TOKENS,
    OLLAMA_TIMEOUT_SECONDS,
    OLLAMA_DEFAULT_NUM_CTX,
    OLLAMA_STREAM_FLAG,
    OLLAMA_NUM_PREDICT_KEY,
    OLLAMA_GENERATE_PATH,
)
from rag_project.rag_core.ports.llm_port import LLMProvider
from rag_project.logger import get_logger


logger = get_logger(__name__)


class OllamaLLMProvider(LLMProvider):
    def __init__(
        self,
        base_url: str,
        model: str,
        fallback_model: Optional[str] = None,
        timeout: float = OLLAMA_TIMEOUT_SECONDS,
        num_ctx: int = OLLAMA_DEFAULT_NUM_CTX,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.fallback_model = fallback_model or model
        self.timeout = timeout

        self.client = httpx.Client(base_url=self.base_url, timeout=self.timeout)
        logger.info(
            "Ollama client initialized base_url=%s model=%s fallback=%s",
            self.base_url,
            self.model,
            self.fallback_model,
        )

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = LLM_DEFAULT_MAX_TOKENS,
    ) -> str:
        target_model = model or self.model
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": OLLAMA_STREAM_FLAG,
            "options": {OLLAMA_NUM_PREDICT_KEY: max_tokens},
        }
        try:
            resp = httpx.post(
                f"{self.base_url}{OLLAMA_GENERATE_PATH}",
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.debug(
                "Ollama response ok model=%s tokens=%d", target_model, max_tokens
            )
            return data.get("response", "")
        except httpx.HTTPError as exc:
            logger.warning(
                "Ollama primary model failed (%s), trying fallback=%s",
                exc,
                self.fallback_model,
            )
            if target_model != self.fallback_model:
                payload["model"] = self.fallback_model
                resp = httpx.post(
                    f"{self.base_url}{OLLAMA_GENERATE_PATH}",
                    json=payload,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info("Fallback Ollama model succeeded: %s", self.fallback_model)
                return data.get("response", "")
            logger.error(
                "Ollama call failed with no fallback remaining: %s", exc, exc_info=True
            )
            raise
