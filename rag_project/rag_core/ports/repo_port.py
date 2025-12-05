from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from rag_project.rag_core.domain.models import (
    Chunk,
    CompanyInfo,
    Document,
    JobPosting,
    PersonalDocument,
    RetrievedChunk,
)
from rag_project.config import (
    REPO_SEARCH_DEFAULT_LIMIT,
    REPO_SEARCH_DEFAULT_MIN_MATCH,
    REPO_SEARCH_DEFAULT_POSTED_AFTER,
    REPO_SEARCH_DEFAULT_DOC_TYPES,
)


class DocumentRepository(ABC):
    @abstractmethod
    def insert_document(self, document: Document) -> None:
        raise NotImplementedError

    @abstractmethod
    def insert_job_posting(self, job_posting: JobPosting) -> None:
        raise NotImplementedError

    @abstractmethod
    def insert_personal_document(self, personal: PersonalDocument) -> None:
        raise NotImplementedError

    @abstractmethod
    def insert_company_info(self, company: CompanyInfo) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_document(self, document_id: UUID) -> None:
        raise NotImplementedError


class ChunkRepository(ABC):
    @abstractmethod
    def insert_chunks_with_embeddings(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        limit: int = REPO_SEARCH_DEFAULT_LIMIT,
        min_match_score: float = REPO_SEARCH_DEFAULT_MIN_MATCH,
        posted_after: float | None = REPO_SEARCH_DEFAULT_POSTED_AFTER,
        doc_types: list[str] | None = REPO_SEARCH_DEFAULT_DOC_TYPES,
    ) -> List[RetrievedChunk]:
        """Return retrieved chunks with associated document/subtype info. posted_after is a unix timestamp (seconds)."""
        raise NotImplementedError
