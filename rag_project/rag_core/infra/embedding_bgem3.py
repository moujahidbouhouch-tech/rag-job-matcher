from typing import List

from sentence_transformers import SentenceTransformer

from rag_project.config import EMBEDDING_MODEL_ID
from rag_project.rag_core.ports.embedding_port import EmbeddingProvider
from rag_project.logger import get_logger


logger = get_logger(__name__)


class BgeM3EmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_id: str = EMBEDDING_MODEL_ID) -> None:
        self.model = SentenceTransformer(model_id)
        logger.info("Loaded embedding model %s", model_id)

    def embed(self, texts: List[str]) -> List[List[float]]:
        # normalize to unit length for cosine similarity
        logger.debug("Embedding batch size=%d", len(texts))
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return [emb.tolist() for emb in embeddings]
    
    def embed_query(self, text: str) -> List[float]:
            """Helper to embed a single query string."""
            return self.embed([text])[0]
