from uuid import uuid4

from rag_project.rag_core.domain.models import Chunk, Document, JobPosting, RetrievedChunk
from rag_project.config import (
    SUPPORTED_DOC_TYPES,
    REPO_SEARCH_DEFAULT_LIMIT,
    REPO_SEARCH_DEFAULT_MIN_MATCH,
    REPO_SEARCH_DEFAULT_POSTED_AFTER,
    REPO_SEARCH_DEFAULT_DOC_TYPES,
    TEST_MIN_MATCH_THRESHOLD,
)
from rag_project.rag_core.retrieval.service import QueryService
from rag_project.rag_core.retrieval.search import build_prompt


class _FakeEmbedder:
    def __init__(self):
        self.last = None

    def embed(self, texts):
        self.last = texts
        return [[float(len(t))] for t in texts]


class _FakeChunkRepo:
    def __init__(self):
        self.last_limit = None
        self.search_called = False

    def search(
        self,
        query_embedding,
        limit: int = REPO_SEARCH_DEFAULT_LIMIT,
        min_match_score: float = REPO_SEARCH_DEFAULT_MIN_MATCH,
        posted_after=REPO_SEARCH_DEFAULT_POSTED_AFTER,
        doc_types=REPO_SEARCH_DEFAULT_DOC_TYPES,
    ):
        self.search_called = True
        self.last_limit = limit
        doc = Document(id=uuid4(), doc_type=SUPPORTED_DOC_TYPES[2])
        jp = JobPosting(document_id=doc.id, title="Result")
        chunk = Chunk(id=uuid4(), document_id=doc.id, chunk_index=0, content="body", token_count=1)
        return [RetrievedChunk(chunk=chunk, document=doc, job_posting=jp, score=0.9)]


class _FakeLLM:
    def __init__(self):
        self.last_prompt = None

    def generate(self, prompt, model=None, max_tokens=0):
        self.last_prompt = prompt
        return "answer"


def test_query_service_returns_retrieved_chunk():
    embedder = _FakeEmbedder()
    repo = _FakeChunkRepo()
    service = QueryService(embedder=embedder, llm=None, chunk_repo=repo)  # type: ignore[arg-type]

    results = service.search("question", limit=1)

    assert embedder.last == ["question"]
    assert repo.last_limit == 1
    assert results[0].chunk.content == "body"


def test_query_service_passes_filters_to_repo():
    embedder = _FakeEmbedder()
    repo = _FakeChunkRepo()
    service = QueryService(embedder=embedder, llm=None, chunk_repo=repo)  # type: ignore[arg-type]

    service.search("question", min_match_score=TEST_MIN_MATCH_THRESHOLD, posted_after=123, doc_types=[SUPPORTED_DOC_TYPES[2]])

    assert repo.last_limit == 5


def test_answer_calls_search_and_llm():
    embedder = _FakeEmbedder()
    repo = _FakeChunkRepo()
    llm = _FakeLLM()
    service = QueryService(embedder=embedder, llm=llm, chunk_repo=repo)

    answer = service.answer("question", limit=1)

    assert repo.search_called is True
    assert "question" in llm.last_prompt
    assert answer.answer == "answer"


def test_build_prompt_includes_chunks():
    doc = Document(id=uuid4(), doc_type=SUPPORTED_DOC_TYPES[0])
    jp = JobPosting(document_id=doc.id, title="DocTitle", company="Co")
    chunk = Chunk(id=uuid4(), document_id=doc.id, chunk_index=0, content="ctx", token_count=1)
    rc = RetrievedChunk(chunk=chunk, document=doc, job_posting=jp, score=0.9)

    prompt = build_prompt("q", [rc])

    assert "DocTitle" in prompt
    assert "ctx" in prompt
    assert "q" in prompt
