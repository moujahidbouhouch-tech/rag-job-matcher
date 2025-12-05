import json
from dataclasses import dataclass
from uuid import uuid4

from rag_project.rag_core.retrieval.job_matching_service import JobMatchingService
from rag_project.rag_core.domain.models import (
    JobRequirement,
    RequirementEvaluation,
    JobMatchResult,
    Chunk,
    Document,
    RetrievedChunk,
    JobPosting,
)
from rag_project.rag_core.ports.llm_port import LLMProvider
from rag_project.rag_core.ports.embedding_port import EmbeddingProvider
from rag_project.rag_core.ports.repo_port import ChunkRepository


class FakeLLM(LLMProvider):
    def __init__(self, responses):
        self.responses = responses

    def generate(self, prompt: str, model=None, max_tokens: int = 256) -> str:
        if self.responses:
            return self.responses.pop(0)
        return ""


class FakeEmbedder(EmbeddingProvider):
    def embed(self, texts):
        return [[0.1] * 3 for _ in texts]

    def embed_query(self, text):
        return [0.1, 0.1, 0.1]


@dataclass
class _Stored:
    chunk: Chunk
    doc: Document
    jp: JobPosting
    score: float


class FakeRepo(ChunkRepository):
    def __init__(self, stored):
        self.stored = stored

    def insert_document(self, document):
        raise NotImplementedError

    def insert_job_posting(self, job_posting):
        raise NotImplementedError

    def insert_personal_document(self, personal):
        raise NotImplementedError

    def insert_company_info(self, company):
        raise NotImplementedError

    def delete_document(self, document_id):
        raise NotImplementedError

    def insert_chunks_with_embeddings(self, chunks, embeddings):
        raise NotImplementedError

    def search(self, query_embedding, limit=5, min_match_score=0.0, posted_after=None, doc_types=None, filters=None):
        return [
            RetrievedChunk(
                chunk=item.chunk,
                document=item.doc,
                job_posting=item.jp,
                personal=None,
                company_info=None,
                score=item.score,
            )
            for item in self.stored[:limit]
        ]


def test_job_matching_service_returns_match_result():
    extraction_json = json.dumps(
        {
            "requirements": [
                {
                    "name": "Python",
                    "category": "Hard Skill",
                    "search_query": "Python programming",
                    "inference_rule": "Check Python experience",
                }
            ]
        }
    )
    evaluation_response = "✅ MATCH | Evidence shows Python"
    llm = FakeLLM([extraction_json, evaluation_response])
    embedder = FakeEmbedder()

    doc = Document(id=uuid4(), doc_type="cv")
    chunk = Chunk(document_id=doc.id, chunk_index=0, content="Python developer experience")
    stored = [_Stored(chunk=chunk, doc=doc, jp=JobPosting(document_id=doc.id), score=0.9)]
    repo = FakeRepo(stored)

    service = JobMatchingService(embedder=embedder, llm=llm, chunk_repo=repo)
    result: JobMatchResult = service.analyze_match("Python job description text")

    assert result.match_count == 1
    assert result.extracted_requirements[0].name == "Python"
    assert isinstance(result.evaluations[0], RequirementEvaluation)
    assert "MATCH" in result.evaluations[0].verdict
