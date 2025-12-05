from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """Abstraction for turning text into embedding vectors."""

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts; returns one vector per text."""
        raise NotImplementedError
