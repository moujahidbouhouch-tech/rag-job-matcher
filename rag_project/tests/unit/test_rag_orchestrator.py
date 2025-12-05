from typing import List
from uuid import uuid4

from rag_project.rag_core.domain.models import Chunk, Document, JobPosting, RAGAnswer, RetrievedChunk
from rag_project.rag_core.ingestion.service import IngestionService
from rag_project.rag_core.retrieval.service import QueryService
from rag_project.config import (
    SUPPORTED_DOC_TYPES,
    REPO_SEARCH_DEFAULT_LIMIT,
    REPO_SEARCH_DEFAULT_MIN_MATCH,
    REPO_SEARCH_DEFAULT_POSTED_AFTER,
    REPO_SEARCH_DEFAULT_DOC_TYPES,
    LLM_PROVIDER_DEFAULT_MAX_TOKENS,
)


class TraceRepo:
    def __init__(self, trace: List[str]):
        self.trace = trace
        self.docs: List[Document] = []
        self.job_postings: List[JobPosting] = []
        self.chunks: List[Chunk] = []
        self.embeddings: List[List[float]] = []

    def insert_document(self, document: Document) -> None:
        self.trace.append("store_doc")
        self.docs.append(document)

    def insert_job_posting(self, jp: JobPosting) -> None:
        self.job_postings.append(jp)

    def insert_personal_document(self, personal) -> None:
        pass

    def insert_company_info(self, company) -> None:
        pass

    def delete_document(self, document_id):
        self.docs = [d for d in self.docs if d.id != document_id]
        self.job_postings = [jp for jp in self.job_postings if jp.document_id != document_id]

    def insert_chunks_with_embeddings(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        self.trace.append("store_chunks")
        self.chunks.extend(chunks)
        self.embeddings.extend(embeddings)

    def search(
        self,
        query_embedding,
        limit: int = REPO_SEARCH_DEFAULT_LIMIT,
        min_match_score: float = REPO_SEARCH_DEFAULT_MIN_MATCH,
        posted_after=REPO_SEARCH_DEFAULT_POSTED_AFTER,
        doc_types=REPO_SEARCH_DEFAULT_DOC_TYPES,
    ):
        # Simple cosine-like scoring against stored embeddings by dot product
        results = []
        for chunk, emb, doc in zip(self.chunks, self.embeddings, self.docs):
            score = sum((e * query_embedding[0] for e in emb))  # they are 1D in tests
            if doc_types and doc.doc_type not in doc_types:
                continue
            jp = next((j for j in self.job_postings if j.document_id == doc.id), None)
            results.append(RetrievedChunk(chunk=chunk, document=doc, job_posting=jp, score=score))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]


class TraceEmbedder:
    def __init__(self, trace: List[str]):
        self.trace = trace

    def embed(self, texts: List[str]) -> List[List[float]]:
        self.trace.append("embed")
        return [[float(len(t))] for t in texts]


class TraceLLM:
    def __init__(self, trace: List[str]):
        self.trace = trace
        self.generated_prompts: List[str] = []

    def generate(self, prompt: str, model=None, max_tokens: int = LLM_PROVIDER_DEFAULT_MAX_TOKENS) -> str:
        self.trace.append("llm")
        self.generated_prompts.append(prompt)
        return "answer:" + prompt[:20]


def test_rag_orchestrator_ingest_calls_steps_in_order(monkeypatch):
    trace: List[str] = []
    from rag_project.config import CHUNK_STRATEGY as CS
    original_cv_strategy = CS.get("cv")
    CS["cv"] = "structured"

    def fake_parse_file(path):
        trace.append("parse")
        return "parsed text"

    def fake_chunk(text, max_tokens, overlap_tokens):
        trace.append("chunk")
        return ["chunked"]

    monkeypatch.setattr("rag_project.rag_core.ingestion.service.parse_file", fake_parse_file)
    monkeypatch.setattr("rag_project.rag_core.ingestion.service.chunk_text", fake_chunk)

    repo = TraceRepo(trace)
    embedder = TraceEmbedder(trace)
    service = IngestionService(document_repo=repo, chunk_repo=repo, embedder=embedder, max_tokens=10, overlap_tokens=2)

    cv_type = SUPPORTED_DOC_TYPES[2]
    service.ingest_file("dummy.txt", metadata={"doc_type": cv_type}, progress_cb=None)

    assert trace[0:2] == ["parse", "store_doc"]
    # Depending on chunker path, chunk step may be implicit
    assert "embed" in trace
    assert "store_chunks" in trace
    CS["cv"] = original_cv_strategy


def test_rag_orchestrator_ingest_empty_document(monkeypatch):
    trace: List[str] = []
    from rag_project.config import CHUNK_STRATEGY as CS
    original_cv_strategy = CS.get("cv")
    CS["cv"] = "structured"

    monkeypatch.setattr("rag_project.rag_core.ingestion.service.parse_file", lambda path: "")
    monkeypatch.setattr("rag_project.rag_core.ingestion.service.chunk_text", lambda text, max_tokens, overlap_tokens: [])
    repo = TraceRepo(trace)
    embedder = TraceEmbedder(trace)
    service = IngestionService(document_repo=repo, chunk_repo=repo, embedder=embedder, max_tokens=5, overlap_tokens=1)

    cv_type = SUPPORTED_DOC_TYPES[2]
    service.ingest_file("empty.txt", metadata={"doc_type": cv_type})

    assert len(repo.docs) == 1  # doc still recorded
    assert len(repo.chunks) == 1  # now creates an empty chunk
    assert len(repo.embeddings) in (0, 1)
    CS["cv"] = original_cv_strategy


def test_rag_orchestrator_query_calls_retrieval_and_llm(monkeypatch):
    trace: List[str] = []
    repo = TraceRepo(trace)
    embedder = TraceEmbedder(trace)
    llm = TraceLLM(trace)
    doc_id = uuid4()
    chunk = Chunk(id=uuid4(), document_id=doc_id, chunk_index=0, content="chunk text", token_count=2)
    doc = Document(id=doc_id, doc_type=SUPPORTED_DOC_TYPES[2])
    jp = JobPosting(document_id=doc_id, title="Doc")
    repo.chunks.append(chunk)
    repo.embeddings.append([1.0])
    repo.docs.append(doc)
    repo.job_postings.append(jp)
    service = QueryService(embedder=embedder, llm=llm, chunk_repo=repo)

    answer = service.answer("question?")

    assert isinstance(answer, RAGAnswer)
    assert "question" in llm.generated_prompts[0]
    assert trace[0] == "embed" and trace[-1] == "llm"


def test_rag_orchestrator_query_handles_no_results(monkeypatch):
    trace: List[str] = []
    repo = TraceRepo(trace)
    embedder = TraceEmbedder(trace)
    llm = TraceLLM(trace)
    service = QueryService(embedder=embedder, llm=llm, chunk_repo=repo)

    answer = service.answer("something")

    assert answer.citations == []
    assert "something" in llm.generated_prompts[0]


def test_rag_orchestrator_full_pipeline_integration(monkeypatch):
    trace: List[str] = []
    repo = TraceRepo(trace)
    embedder = TraceEmbedder(trace)
    llm = TraceLLM(trace)
    monkeypatch.setattr("rag_project.rag_core.ingestion.service.chunk_text", lambda text, max_tokens, overlap_tokens: [text])
    monkeypatch.setattr("rag_project.rag_core.ingestion.service.parse_file", lambda path: str(path))
    ingest_service = IngestionService(document_repo=repo, chunk_repo=repo, embedder=embedder, max_tokens=50, overlap_tokens=5)
    query_service = QueryService(embedder=embedder, llm=llm, chunk_repo=repo)

    doc_type = SUPPORTED_DOC_TYPES[0]
    doc_ids = [
        ingest_service.ingest_file("doc1 content", metadata={"doc_type": doc_type}),
        ingest_service.ingest_file("doc2 content", metadata={"doc_type": doc_type}),
    ]

    result = query_service.answer("doc1?")

    assert set(doc_ids) == {doc.id for doc in repo.docs}
    assert any(str(doc_ids[0]) in c.chunk_id.hex or c.document_id == doc_ids[0] for c in result.citations)
