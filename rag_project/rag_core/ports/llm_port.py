from abc import ABC, abstractmethod
from typing import Optional

from rag_project.config import LLM_PROVIDER_DEFAULT_MAX_TOKENS


class LLMProvider(ABC):
    """Abstraction for calling an LLM."""

    @abstractmethod
    def generate(self, prompt: str, model: Optional[str] = None, max_tokens: int = LLM_PROVIDER_DEFAULT_MAX_TOKENS) -> str:
        raise NotImplementedError
