import sys
from copy import deepcopy
from pathlib import Path
from typing import List

import pytest

# Ensure project root on path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag_project.config import (  # noqa: E402
    CHUNK_PROFILES,
    CHUNK_STRATEGY,
    CV_CHUNKER_MODEL_ID,
    DOC_TYPE_CV,
    DOC_TYPE_JOB_POSTING,
    DOC_TYPE_THESIS,
    LLM_PROVIDER_DEFAULT_MAX_TOKENS,
)
from rag_project.rag_core.domain.models import Chunk, Document  # noqa: E402
from rag_project.rag_core.ingestion.service import IngestionService  # noqa: E402
from rag_project.rag_core.ports.embedding_port import EmbeddingProvider  # noqa: E402
from rag_project.rag_core.ports.repo_port import ChunkRepository, DocumentRepository  # noqa: E402


class FakeEmbedder(EmbeddingProvider):
    def embed(self, texts: List[str]) -> List[List[float]]:
        return [[float(i)] for i, _ in enumerate(texts)]

    def embed_query(self, text: str) -> List[float]:
        return [0.0]


class FakeDocumentRepo(DocumentRepository):
    def __init__(self):
        self.docs: List[Document] = []
        self.jobs = []
        self.personal = []
        self.company = []

    def insert_document(self, document: Document) -> None:
        self.docs.append(document)

    def insert_job_posting(self, job_posting):
        self.jobs.append(job_posting)

    def insert_personal_document(self, personal):
        self.personal.append(personal)

    def insert_company_info(self, company):
        self.company.append(company)

    def delete_document(self, document_id):
        return None


class FakeChunkRepo(ChunkRepository):
    def __init__(self):
        self.chunks: List[Chunk] = []
        self.embeddings: List[List[float]] = []

    def insert_chunks_with_embeddings(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        self.chunks.extend(chunks)
        self.embeddings.extend(embeddings)

    def search(self, *args, **kwargs):
        return []


class FakeLLM:
    def __init__(self):
        self.calls = []

    def generate(self, prompt: str, model: str | None = None, max_tokens: int | None = LLM_PROVIDER_DEFAULT_MAX_TOKENS):
        self.calls.append({"prompt": prompt, "model": model, "max_tokens": max_tokens})
        if "split_after_lines" in prompt:
            return '{"split_after_lines": [2, 5]}'
        return "{}"


def _load_sample(name: str) -> str:
    path = ROOT / "tests" / "dummy_tests_documents" / name
    return path.read_text(encoding="utf-8")


def test_ingestion_cv_uses_llm_chunker():
    llm = FakeLLM()
    service = IngestionService(
        document_repo=FakeDocumentRepo(),
        chunk_repo=FakeChunkRepo(),
        embedder=FakeEmbedder(),
        max_tokens=50,
        overlap_tokens=10,
        use_structured_chunker=True,
        chunk_profiles=deepcopy(CHUNK_PROFILES),
        llm_provider=llm,
    )

    cv_text_path = ROOT / "tests" / "dummy_tests_documents" / "cv_sample.txt"
    messages = []

    def progress_cb(stage, info):
        if "message" in info:
            messages.append(info["message"])

    doc_id = service.ingest_file(str(cv_text_path), metadata={"doc_type": DOC_TYPE_CV}, progress_cb=progress_cb)

    # CV chunker should have been selected and LLM called with CV chunker model
    assert any("cv llm" in m for m in messages)
    assert any(call["model"] == CV_CHUNKER_MODEL_ID for call in llm.calls)
    assert service.chunk_repo.chunks, "No chunks stored"
    assert len(service.chunk_repo.chunks) == len(service.chunk_repo.embeddings)
    assert service.chunk_repo.chunks[0].document_id == doc_id


def test_ingestion_structured_for_thesis():
    llm = FakeLLM()
    profiles = deepcopy(CHUNK_PROFILES)
    # Ensure thesis profile does not require LLM assist for this test
    profiles.setdefault(DOC_TYPE_THESIS, {}).update({"use_llm": False})

    service = IngestionService(
        document_repo=FakeDocumentRepo(),
        chunk_repo=FakeChunkRepo(),
        embedder=FakeEmbedder(),
        max_tokens=50,
        overlap_tokens=10,
        use_structured_chunker=True,
        structured_use_llm=False,
        chunk_profiles=profiles,
        llm_provider=llm,
    )

    thesis_path = ROOT / "tests" / "dummy_tests_documents" / "thesis_sample.txt"
    messages = []

    def progress_cb(stage, info):
        if "message" in info:
            messages.append(info["message"])

    doc_id = service.ingest_file(str(thesis_path), metadata={"doc_type": DOC_TYPE_THESIS}, progress_cb=progress_cb)

    assert any("structured" in m for m in messages)
    assert service.chunk_repo.chunks, "No chunks stored"
    assert len(service.chunk_repo.chunks) == len(service.chunk_repo.embeddings)
    assert service.chunk_repo.chunks[0].document_id == doc_id


def test_ingestion_structured_for_job_posting():
    llm = FakeLLM()
    profiles = deepcopy(CHUNK_PROFILES)
    profiles.setdefault(DOC_TYPE_JOB_POSTING, {}).update({"use_llm": False})

    service = IngestionService(
        document_repo=FakeDocumentRepo(),
        chunk_repo=FakeChunkRepo(),
        embedder=FakeEmbedder(),
        max_tokens=50,
        overlap_tokens=10,
        use_structured_chunker=True,
        structured_use_llm=False,
        chunk_profiles=profiles,
        llm_provider=llm,
    )

    job_path = ROOT / "tests" / "dummy_tests_documents" / "job_posting_sample.txt"
    messages = []

    def progress_cb(stage, info):
        if "message" in info:
            messages.append(info["message"])

    doc_id = service.ingest_file(str(job_path), metadata={"doc_type": DOC_TYPE_JOB_POSTING}, progress_cb=progress_cb)

    assert any("structured" in m for m in messages)
    assert service.chunk_repo.chunks, "No chunks stored"
    assert len(service.chunk_repo.chunks) == len(service.chunk_repo.embeddings)
    assert service.chunk_repo.chunks[0].document_id == doc_id
