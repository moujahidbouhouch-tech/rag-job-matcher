from typing import List

from rag_project.rag_core.domain.models import RAGAnswer, RetrievedChunk
from rag_project.rag_core.retrieval.search import answer_question, vector_search
from rag_project.rag_core.ports.embedding_port import EmbeddingProvider
from rag_project.rag_core.ports.llm_port import LLMProvider
from rag_project.rag_core.ports.repo_port import ChunkRepository
from rag_project.config import DEFAULT_MIN_MATCH_SCORE, DEFAULT_SEARCH_LIMIT
from rag_project.logger import get_logger


logger = get_logger(__name__)


class QueryService:
    def __init__(
        self,
        embedder: EmbeddingProvider,
        llm: LLMProvider,
        chunk_repo: ChunkRepository,
    ) -> None:
        self.embedder = embedder
        self.llm = llm
        self.chunk_repo = chunk_repo

    def search(
        self,
        question: str,
        limit: int = DEFAULT_SEARCH_LIMIT,
        min_match_score: float = DEFAULT_MIN_MATCH_SCORE,
        posted_after: float | None = None,
        doc_types: list[str] | None = None,
    ) -> List[RetrievedChunk]:
        logger.info(
            "Search requested: limit=%d min_score=%.2f doc_types=%s",
            limit,
            min_match_score,
            doc_types,
        )
        return vector_search(
            question,
            self.embedder,
            self.chunk_repo,
            limit=limit,
            min_match_score=min_match_score,
            posted_after=posted_after,
            doc_types=doc_types,
        )

    def answer(
        self,
        question: str,
        limit: int = DEFAULT_SEARCH_LIMIT,
        min_match_score: float = DEFAULT_MIN_MATCH_SCORE,
        posted_after: float | None = None,
        doc_types: list[str] | None = None,
    ) -> RAGAnswer:
        logger.info(
            "Answer requested: limit=%d min_score=%.2f doc_types=%s",
            limit,
            min_match_score,
            doc_types,
        )
        return answer_question(
            question,
            self.embedder,
            self.llm,
            self.chunk_repo,
            limit=limit,
            min_match_score=min_match_score,
            posted_after=posted_after,
            doc_types=doc_types,
        )
