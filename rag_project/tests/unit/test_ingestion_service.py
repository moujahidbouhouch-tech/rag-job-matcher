from pathlib import Path
from typing import List

import json

from rag_project.rag_core.ingestion.service import IngestionService
from rag_project.rag_core.ingestion.chunker import chunk_text
from rag_project.rag_core.ports.embedding_port import EmbeddingProvider
from rag_project.rag_core.ports.repo_port import ChunkRepository, DocumentRepository
from rag_project.rag_core.domain.models import Chunk, Document
from rag_project.config import (
    SUPPORTED_DOC_TYPES,
    REPO_SEARCH_DEFAULT_LIMIT,
    REPO_SEARCH_DEFAULT_MIN_MATCH,
    REPO_SEARCH_DEFAULT_POSTED_AFTER,
    REPO_SEARCH_DEFAULT_DOC_TYPES,
)


class FakeEmbedder(EmbeddingProvider):
    def embed(self, texts: List[str]) -> List[List[float]]:
        return [[float(i)] for i, _ in enumerate(texts)]


class FakeDocumentRepo(DocumentRepository):
    def __init__(self) -> None:
        self.inserted_docs: List[Document] = []
        self.deleted: List[str] = []
        self.job_postings: List[dict] = []
        self.personal_docs: List[dict] = []
        self.company_info: List[dict] = []

    def insert_document(self, document: Document) -> None:
        self.inserted_docs.append(document)

    def insert_job_posting(self, job_posting) -> None:
        self.job_postings.append(job_posting.__dict__)

    def insert_personal_document(self, personal) -> None:
        self.personal_docs.append(personal.__dict__)

    def insert_company_info(self, company) -> None:
        self.company_info.append(company.__dict__)

    def delete_document(self, document_id):
        self.deleted.append(document_id)


class FakeChunkRepo(ChunkRepository):
    def __init__(self) -> None:
        self.inserted_chunks: List[Chunk] = []
        self.inserted_embeddings: List[List[float]] = []

    def insert_chunks_with_embeddings(
        self, chunks: List[Chunk], embeddings: List[List[float]]
    ) -> None:
        self.inserted_chunks.extend(chunks)
        self.inserted_embeddings.extend(embeddings)

    def search(
        self,
        query_embedding,
        limit: int = REPO_SEARCH_DEFAULT_LIMIT,
        min_match_score: float = REPO_SEARCH_DEFAULT_MIN_MATCH,
        posted_after=REPO_SEARCH_DEFAULT_POSTED_AFTER,
        doc_types=REPO_SEARCH_DEFAULT_DOC_TYPES,
    ):
        return []


def load_sample_job_text() -> str:
    sample_path = (
        Path(__file__).resolve().parents[1]
        / "dummy_tests_documents"
        / "json_jobs_documents.json"
    )
    with open(sample_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    job = data["jobs"][0]
    # Increase length by repeating the description
    return f"{job['title']}\n\n{job['description']}\n\n{job['description']}"


def load_cv_text() -> str:
    sample_path = (
        Path(__file__).resolve().parents[1] / "dummy_tests_documents" / "cv_sample.txt"
    )
    return sample_path.read_text(encoding="utf-8", errors="ignore")


def test_ingestion_service_creates_job_and_chunks():
    embedder = FakeEmbedder()
    doc_repo = FakeDocumentRepo()
    chunk_repo = FakeChunkRepo()
    service = IngestionService(
        document_repo=doc_repo,
        chunk_repo=chunk_repo,
        embedder=embedder,
        max_tokens=80,
        overlap_tokens=20,
    )

    text = load_sample_job_text()
    from rag_project.config import DOC_TYPE_JOB_POSTING

    job_id = service._ingest_text(
        text,
        metadata={"source": "test", "doc_type": DOC_TYPE_JOB_POSTING},
        progress_cb=None,
    )

    assert doc_repo.inserted_docs, "Document was not inserted"
    assert doc_repo.inserted_docs[0].id == job_id
    assert len(chunk_repo.inserted_chunks) == len(chunk_repo.inserted_embeddings)
    # Should produce multiple chunks for long text
    assert len(chunk_repo.inserted_chunks) > 1
    for chunk in chunk_repo.inserted_chunks:
        assert chunk.document_id == job_id
        assert chunk.content.strip()


def test_ingestion_service_ingests_file_and_chunks():
    tmp = Path("rag_project/tests/unit/tmp_cv.txt")
    tmp.write_text(load_cv_text(), encoding="utf-8")
    from rag_project.config import CHUNK_STRATEGY as CS

    original_cv_strategy = CS.get("cv")
    CS["cv"] = "structured"

    embedder = FakeEmbedder()
    doc_repo = FakeDocumentRepo()
    chunk_repo = FakeChunkRepo()
    service = IngestionService(
        document_repo=doc_repo,
        chunk_repo=chunk_repo,
        embedder=embedder,
        max_tokens=50,
        overlap_tokens=12,
    )

    job_id = service.ingest_file(
        str(tmp), metadata={"doc_type": SUPPORTED_DOC_TYPES[2]}
    )

    assert doc_repo.inserted_docs and doc_repo.inserted_docs[0].id == job_id
    assert doc_repo.inserted_docs[0].doc_type == SUPPORTED_DOC_TYPES[2]
    assert chunk_repo.inserted_chunks, "No chunks created from file"
    CS["cv"] = original_cv_strategy
    tmp.unlink()
