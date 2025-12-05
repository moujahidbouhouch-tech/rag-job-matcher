from uuid import uuid4

from rag_project.rag_core.retrieval.job_matching_service import JobMatchingService
from rag_project.config import CITATION_TOP_K
from rag_project.rag_core.domain.models import JobRequirement


class FakeLLM:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def generate(self, prompt, model=None, max_tokens=0):
        self.calls.append({"prompt": prompt, "model": model, "max_tokens": max_tokens})
        return self.responses.pop(0)


class FakeEmbedder:
    def embed(self, texts):
        return [[0.1] * 3 for _ in texts]

    def embed_query(self, text):
        return [0.1, 0.2, 0.3]


class FakeChunk:
    def __init__(self, doc_id):
        self.id = uuid4()
        self.document_id = doc_id
        self.chunk_index = 0
        self.content = "evidence"
        self.token_count = 1


class FakeDoc:
    def __init__(self, doc_type="cv"):
        self.id = uuid4()
        self.doc_type = doc_type
        self.metadata = {}


class FakeRetrieved:
    def __init__(self, chunk, doc, score=0.9, title=None, company=None):
        self.chunk = chunk
        self.document = doc
        self.score = score
        self.job_posting = type("JP", (), {"title": title, "company": company})() if title else None
        self.personal = None
        self.company_info = None


class FakeRepo:
    def __init__(self, retrieved):
        self.retrieved = retrieved

    def search(self, query_embedding, limit=5, doc_types=None, min_match_score=0.0, posted_after=None, filters=None):
        return self.retrieved

    def insert_document(self, *args, **kwargs):
        raise NotImplementedError

    def insert_job_posting(self, *args, **kwargs):
        raise NotImplementedError

    def insert_personal_document(self, *args, **kwargs):
        raise NotImplementedError

    def insert_company_info(self, *args, **kwargs):
        raise NotImplementedError

    def delete_document(self, *args, **kwargs):
        raise NotImplementedError


class FakeDomainExtractor:
    def __init__(self, mappings=None):
        self.calls = 0
        self.mappings = mappings

    def extract_domain_mappings(self, job_text):
        self.calls += 1
        return self.mappings


class FakeRequirement:
    def __init__(self, name):
        self.name = name
        self.category = "Hard Skill"
        self.search_query = name
        self.inference_rule = "rule"


class FakeJobMatchingService(JobMatchingService):
    def _extract_requirements(self, job_text):  # override to bypass LLM extraction
        return [FakeRequirement("req1"), FakeRequirement("req2")]


def _make_service(domain_mappings=None, retrieved=None, llm_responses=None):
    llm_responses = llm_responses or ["{}", "✅ MATCH | ok", "✅ MATCH | ok"]
    repo = FakeRepo(retrieved or [])
    service = FakeJobMatchingService(
        embedder=FakeEmbedder(),
        llm=FakeLLM(llm_responses),
        chunk_repo=repo,
        domain_extractor=FakeDomainExtractor(domain_mappings),
    )
    return service


def test_analyze_extracts_domain_mappings_once():
    service = _make_service()
    service.analyze_match("job")
    assert service.domain_extractor.calls == 1


def test_analyze_uses_extracted_mappings_in_evaluations():
    mappings = type("DM", (), {"language_mappings": ["x"], "skill_demonstrations": [], "credential_mappings": []})()
    service = _make_service(domain_mappings=mappings)
    result = service.analyze_match("job")
    assert result.evaluations  # evaluations produced


def test_analyze_continues_when_domain_extraction_fails():
    class FailingExtractor:
        def extract_domain_mappings(self, job_text):
            raise RuntimeError("fail")
    service = _make_service(domain_mappings=None)
    service.domain_extractor = FailingExtractor()
    result = service.analyze_match("job")
    assert result.evaluations


def test_citations_respect_top_k():
    doc = FakeDoc()
    retrieved = [FakeRetrieved(FakeChunk(doc.id), doc) for _ in range(CITATION_TOP_K + 2)]
    service = _make_service(retrieved=retrieved)
    result = service.analyze_match("job")
    assert result.evaluations[0].citations is not None
    assert len(result.evaluations[0].citations) == CITATION_TOP_K


def test_citations_contain_chunk_metadata():
    doc = FakeDoc()
    chunk = FakeChunk(doc.id)
    retrieved = [FakeRetrieved(chunk, doc, score=0.8, title="t", company="c")]
    service = _make_service(retrieved=retrieved)
    result = service.analyze_match("job")
    cite = result.evaluations[0].citations[0]
    assert cite["chunk_id"] and cite["doc_id"]
    assert cite["doc_type"] == doc.doc_type
    assert cite["title"] == "t"


def test_evaluation_prompt_includes_domain_mappings():
    from rag_project.rag_core.retrieval.domain_extraction_service import DomainMapping

    mappings = DomainMapping(
        language_mappings=[{"source_term": "Masterarbeit", "equivalent_terms": ["Master's thesis"], "context": "academic"}],
        skill_demonstrations=[],
        credential_mappings=[],
    )
    llm = FakeLLM(["{}", "✅ MATCH | ok"])  # first call unused in overridden _extract_requirements
    repo = FakeRepo([FakeRetrieved(FakeChunk(FakeDoc().id), FakeDoc())])
    service = FakeJobMatchingService(
        embedder=FakeEmbedder(),
        llm=llm,
        chunk_repo=repo,
        domain_extractor=FakeDomainExtractor(mappings),
    )

    service.analyze_match("job requiring thesis")

    eval_prompt = llm.calls[-1]["prompt"]
    assert "Masterarbeit" in eval_prompt
    assert "Master's thesis" in eval_prompt
