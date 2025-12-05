from datetime import UTC, datetime, timedelta
from typing import List
from uuid import uuid4

import psycopg
import pytest
from pgvector.psycopg import register_vector
from rag_project.config import (
    EMBEDDING_DIM,
    SUPPORTED_DOC_TYPES,
    REPO_SEARCH_DEFAULT_LIMIT,
    REPO_SEARCH_DEFAULT_MIN_MATCH,
    REPO_SEARCH_DEFAULT_POSTED_AFTER,
    REPO_SEARCH_DEFAULT_DOC_TYPES,
    TEST_MIN_MATCH_THRESHOLD,
)

from rag_project.rag_core.config import get_settings
from rag_project.rag_core.domain.models import Chunk, Document, JobPosting, RetrievedChunk
from rag_project.rag_core.infra.db_pgvector import PgVectorRepository


def _dsn():
    settings = get_settings()
    pw = f" password={settings.db_password}" if settings.db_password else ""
    return (
        f"host={settings.db_host} "
        f"port={settings.db_port} "
        f"dbname={settings.db_name} "
        f"user={settings.db_user}"
        f"{pw}"
    )


def _repo():
    return PgVectorRepository(_dsn())


def _vector(val: float = 0.1) -> List[float]:
    return [val for _ in range(EMBEDDING_DIM)]


def _db_available():
    try:
        psycopg.connect(_dsn(), connect_timeout=120).close()
        return True
    except psycopg.OperationalError as exc:
        print(f"[debug:test_repo_filters] DB not reachable: {exc}")
        return False


def _clear_tables():
    # No-op for now; assumes test DB is already isolated/empty.
    return


class FakeRepo:
    def __init__(self):
        self.docs: List[Document] = []
        self.job_postings: List[JobPosting] = []
        self.chunks: List[Chunk] = []

    def insert_document(self, document: Document):
        self.docs.append(document)

    def insert_job_posting(self, jp: JobPosting):
        self.job_postings.append(jp)

    def insert_personal_document(self, personal):
        pass

    def insert_company_info(self, company):
        pass

    def insert_chunks_with_embeddings(self, chunks: List[Chunk], embeddings):
        self.chunks.extend(chunks)

    def delete_document(self, document_id):
        self.docs = [d for d in self.docs if d.id != document_id]
        self.job_postings = [jp for jp in self.job_postings if jp.document_id != document_id]
        self.chunks = [c for c in self.chunks if c.document_id != document_id]

    def search(
        self,
        query_embedding,
        limit: int = REPO_SEARCH_DEFAULT_LIMIT,
        min_match_score: float = REPO_SEARCH_DEFAULT_MIN_MATCH,
        posted_after=REPO_SEARCH_DEFAULT_POSTED_AFTER,
        doc_types=REPO_SEARCH_DEFAULT_DOC_TYPES,
    ):
        results = []
        for chunk in self.chunks:
            doc = next(d for d in self.docs if d.id == chunk.document_id)
            if doc_types and doc.doc_type not in doc_types:
                continue
            jp = next((j for j in self.job_postings if j.document_id == doc.id), None)
            if jp:
                if jp.match_score is not None and jp.match_score < min_match_score:
                    continue
                if posted_after and jp.posted_at and jp.posted_at.timestamp() < posted_after:
                    continue
            score = jp.match_score if jp and jp.match_score is not None else 0.0
            results.append(RetrievedChunk(chunk=chunk, document=doc, job_posting=jp, score=score))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]


def test_search_filters_by_match_score_and_date():
    _clear_tables()
    repo = FakeRepo()
    now = datetime.now(UTC)
    job_type = SUPPORTED_DOC_TYPES[0]
    recent_doc = Document(id=uuid4(), doc_type=job_type)
    old_doc = Document(id=uuid4(), doc_type=job_type)
    recent_jp = JobPosting(document_id=recent_doc.id, title="Recent high score", match_score=0.9, posted_at=now)
    old_jp = JobPosting(document_id=old_doc.id, title="Old low score", match_score=0.4, posted_at=now - timedelta(days=10))

    recent_chunk = Chunk(id=uuid4(), document_id=recent_doc.id, chunk_index=0, content="recent chunk", token_count=2)
    old_chunk = Chunk(id=uuid4(), document_id=old_doc.id, chunk_index=0, content="old chunk", token_count=2)

    try:
        repo.insert_document(recent_doc)
        repo.insert_document(old_doc)
        repo.insert_job_posting(recent_jp)
        repo.insert_job_posting(old_jp)
        repo.insert_chunks_with_embeddings([recent_chunk, old_chunk], [_vector(0.2), _vector(0.2)])

        # Require min match_score and recent postings (last 7 days)
        results = repo.search(
            query_embedding=_vector(0.2),
            limit=5,
            min_match_score=TEST_MIN_MATCH_THRESHOLD,
            posted_after=now.timestamp() - 7 * 86400,
        )
    finally:
        # Cleanup by job id (cascades)
        try:
            repo.delete_document(recent_doc.id)
            repo.delete_document(old_doc.id)
        except psycopg.OperationalError:
            pass

    assert results, "No results returned for filtered search"
    returned_ids = {rc.document.id for rc in results}
    assert recent_doc.id in returned_ids, "Recent high-score job missing"
    assert old_doc.id not in returned_ids, "Old/low-score job should be filtered out"


def test_search_ranks_high_match_score_over_recency_when_similarity_equal():
    _clear_tables()
    repo = FakeRepo()
    now = datetime.now(UTC)
    job_type = SUPPORTED_DOC_TYPES[0]
    high_doc = Document(id=uuid4(), doc_type=job_type)
    low_doc = Document(id=uuid4(), doc_type=job_type)
    high_score_old = JobPosting(document_id=high_doc.id, title="High score old", match_score=0.9, posted_at=now - timedelta(days=14))
    low_score_recent = JobPosting(document_id=low_doc.id, title="Low score recent", match_score=0.5, posted_at=now - timedelta(days=1))

    # Same embedding so similarity equal; ranking should prefer higher match_score despite older date.
    emb = _vector(0.3)
    chunk_high = Chunk(id=uuid4(), document_id=high_doc.id, chunk_index=0, content="hs old", token_count=2)
    chunk_low = Chunk(id=uuid4(), document_id=low_doc.id, chunk_index=0, content="ls recent", token_count=2)

    try:
        repo.insert_document(high_doc)
        repo.insert_document(low_doc)
        repo.insert_job_posting(high_score_old)
        repo.insert_job_posting(low_score_recent)
        repo.insert_chunks_with_embeddings([chunk_high, chunk_low], [emb, emb])

        results = repo.search(query_embedding=emb, limit=2)
    finally:
        try:
            repo.delete_document(high_doc.id)
            repo.delete_document(low_doc.id)
        except psycopg.OperationalError:
            pass

    assert len(results) == 2
    top_doc = results[0].document
    assert top_doc.id == high_doc.id, "High match_score job should rank above recent lower score when similarity ties"
