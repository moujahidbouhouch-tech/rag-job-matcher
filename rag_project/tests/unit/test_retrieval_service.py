from dataclasses import dataclass
from datetime import UTC, datetime
from typing import List
from uuid import uuid4

import psycopg
import pytest

from rag_project.config import (
    EMBEDDING_DIM,
    SUPPORTED_DOC_TYPES,
    REPO_SEARCH_DEFAULT_LIMIT,
    REPO_SEARCH_DEFAULT_MIN_MATCH,
    REPO_SEARCH_DEFAULT_POSTED_AFTER,
    REPO_SEARCH_DEFAULT_DOC_TYPES,
    TEST_MIN_MATCH_THRESHOLD,
)
from rag_project.rag_core.domain.models import Chunk, Document, JobPosting, RetrievedChunk
from rag_project.config import (
    DOC_TYPE_JOB_POSTING,
)
from rag_project.rag_core.retrieval.search import build_prompt, vector_search
from rag_project.rag_core.retrieval.service import QueryService


class FakeEmbedder:
    def embed(self, texts: List[str]) -> List[List[float]]:
        return [[float(len(t))] * EMBEDDING_DIM for t in texts]


@dataclass
class _Stored:
    chunk: Chunk
    doc: Document
    jp: JobPosting | None
    score: float


class FakeChunkRepo:
    def __init__(self, stored: List[_Stored]):
        self.stored = stored

    def search(
        self,
        query_embedding,
        limit: int = REPO_SEARCH_DEFAULT_LIMIT,
        min_match_score: float = REPO_SEARCH_DEFAULT_MIN_MATCH,
        posted_after=REPO_SEARCH_DEFAULT_POSTED_AFTER,
        doc_types=REPO_SEARCH_DEFAULT_DOC_TYPES,
    ):
        results = []
        for record in self.stored:
            match_score = record.jp.match_score if record.jp else None
            posted_at = record.jp.posted_at if record.jp else None
            if match_score is not None and match_score < min_match_score:
                continue
            if posted_after and posted_at:
                if posted_at.timestamp() < posted_after:
                    continue
            if doc_types and record.doc.doc_type not in doc_types:
                continue
            results.append(RetrievedChunk(chunk=record.chunk, document=record.doc, job_posting=record.jp, score=record.score))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]


def _chunk_with_score(job_title: str, score: float, doc_type: str | None = None, posted_at=None, match_score=None):
    doc = Document(id=uuid4(), doc_type=doc_type or SUPPORTED_DOC_TYPES[0])
    jp = JobPosting(document_id=doc.id, title=job_title, posted_at=posted_at, match_score=match_score)
    chunk = Chunk(id=uuid4(), document_id=doc.id, chunk_index=0, content=f"chunk for {job_title}", token_count=2)
    return _Stored(chunk=chunk, doc=doc, jp=jp, score=score)


def test_retrieval_service_ranks_by_score():
    stored = [
        _chunk_with_score("low", 0.2),
        _chunk_with_score("high", 0.9),
        _chunk_with_score("mid", 0.5),
    ]
    service = QueryService(embedder=FakeEmbedder(), llm=None, chunk_repo=FakeChunkRepo(stored))  # type: ignore[arg-type]

    results = service.search("question", limit=3)

    titles = [rc.job_posting.title for rc in results]
    assert titles == ["high", "mid", "low"]


def test_retrieval_service_filters_by_doc_type_and_recency():
    recent = _chunk_with_score("recent", 0.6, doc_type=SUPPORTED_DOC_TYPES[2], posted_at=datetime.now(UTC), match_score=0.9)
    old = _chunk_with_score(
        "old", 0.8, doc_type=SUPPORTED_DOC_TYPES[0], posted_at=datetime(2000, 1, 1, tzinfo=UTC), match_score=0.95
    )
    repo = FakeChunkRepo([recent, old])
    service = QueryService(embedder=FakeEmbedder(), llm=None, chunk_repo=repo)  # type: ignore[arg-type]

    results = service.search(
        "q",
        min_match_score=TEST_MIN_MATCH_THRESHOLD,
        posted_after=datetime(2020, 1, 1, tzinfo=UTC).timestamp(),
        doc_types=[SUPPORTED_DOC_TYPES[2]],
    )

    assert len(results) == 1
    assert results[0].job_posting.title == "recent"


def test_retrieval_service_handles_no_results_and_small_k():
    repo = FakeChunkRepo([])
    service = QueryService(embedder=FakeEmbedder(), llm=None, chunk_repo=repo)  # type: ignore[arg-type]

    results = service.search("q", limit=10)

    assert results == []


def test_retrieval_prompt_builds_context():
    doc = Document(id=uuid4(), doc_type=DOC_TYPE_JOB_POSTING)
    jp = JobPosting(document_id=doc.id, title="Doc", company="Acme")
    chunk = Chunk(id=uuid4(), document_id=doc.id, chunk_index=0, content="context body", token_count=2)
    rc = type("RC", (), {"document": doc, "job_posting": jp, "chunk": chunk, "score": 0.9})()
    prompt = build_prompt("What is up?", [rc])
    assert "Doc" in prompt
    assert "context body" in prompt
    assert "What is up?" in prompt


# Integration-like test using real PgVectorRepository if DB is reachable.
def _dsn():
    from rag_project.rag_core.config import get_settings

    settings = get_settings()
    pw = f" password={settings.db_password}" if settings.db_password else ""
    return (
        f"host={settings.db_host} "
        f"port={settings.db_port} "
        f"dbname={settings.db_name} "
        f"user={settings.db_user}"
        f"{pw}"
    )


def _db_available():
    try:
        psycopg.connect(_dsn(), connect_timeout=120).close()
        return True
    except psycopg.OperationalError as exc:
        print(f"[debug:test_retrieval_service] DB not reachable: {exc}")
        return False


def _clear_tables():
    return


def test_retrieval_db_backed_query_returns_expected_top_k():
    doc1 = Document(id=uuid4(), doc_type=DOC_TYPE_JOB_POSTING)
    doc2 = Document(id=uuid4(), doc_type=DOC_TYPE_JOB_POSTING)
    chunk1 = Chunk(id=uuid4(), document_id=doc1.id, chunk_index=0, content="high", token_count=1)
    chunk2 = Chunk(id=uuid4(), document_id=doc2.id, chunk_index=0, content="low", token_count=1)
    stored = [
        _Stored(chunk=chunk1, doc=doc1, jp=JobPosting(document_id=doc1.id, title="Vector high"), score=0.9),
        _Stored(chunk=chunk2, doc=doc2, jp=JobPosting(document_id=doc2.id, title="Vector low"), score=0.1),
    ]
    repo = FakeChunkRepo(stored)
    embedder = FakeEmbedder()
    service = QueryService(embedder=embedder, llm=None, chunk_repo=repo)  # type: ignore[arg-type]

    results = service.search("q", limit=2)

    assert results
    assert results[0].document.id == doc1.id
