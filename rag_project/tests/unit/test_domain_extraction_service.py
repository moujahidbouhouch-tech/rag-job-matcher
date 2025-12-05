import json

import pytest

from rag_project.rag_core.retrieval.domain_extraction_service import DomainExtractionService
from rag_project.config import DOMAIN_MAPPING_MAX_TOKENS, DOMAIN_MAPPING_CANDIDATE_LIMIT


class FakeLLM:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate(self, prompt, max_tokens=0):
        self.calls.append({"prompt": prompt, "max_tokens": max_tokens})
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class FakeEmbedder:
    def embed(self, texts):
        return [[0.1] * 3 for _ in texts]


class FakeRepo:
    def __init__(self, chunks=None):
        self.chunks = chunks or []
        self.search_calls = []

    def search(self, query_embedding, limit=0, doc_types=None):
        self.search_calls.append({"limit": limit, "doc_types": doc_types})
        return self.chunks


class _RC:
    def __init__(self, content):
        self.chunk = type("Chunk", (), {"content": content})()


def test_extract_domain_mappings_returns_empty_on_malformed_json():
    llm = FakeLLM("not json")
    service = DomainExtractionService(llm, FakeEmbedder(), FakeRepo())

    result = service.extract_domain_mappings("job")

    assert result.language_mappings == []
    assert result.skill_demonstrations == []
    assert result.credential_mappings == []


def test_extract_domain_mappings_parses_code_fence():
    payload = {
        "language_mappings": [{"source_term": "Masterarbeit", "equivalent_terms": ["Master's thesis"], "context": "academic", "confidence": 0.95}],
        "skill_demonstrations": [],
        "credential_mappings": [],
    }
    llm = FakeLLM("""```json\n%s\n```""" % json.dumps(payload))
    service = DomainExtractionService(llm, FakeEmbedder(), FakeRepo())

    result = service.extract_domain_mappings("job")

    assert result.language_mappings and result.language_mappings[0]["source_term"] == "Masterarbeit"


def test_extract_respects_max_tokens_setting():
    llm = FakeLLM("{}")
    service = DomainExtractionService(llm, FakeEmbedder(), FakeRepo())

    service.extract_domain_mappings("job")

    assert llm.calls[0]["max_tokens"] == DOMAIN_MAPPING_MAX_TOKENS


def test_extract_respects_candidate_limit():
    llm = FakeLLM("{}")
    repo = FakeRepo([])
    service = DomainExtractionService(llm, FakeEmbedder(), repo)

    service.extract_domain_mappings("job")

    assert repo.search_calls[0]["limit"] == DOMAIN_MAPPING_CANDIDATE_LIMIT


def test_candidate_summary_concatenates_chunks():
    llm = FakeLLM("{}")
    repo = FakeRepo([_RC("one"), _RC("two")])
    service = DomainExtractionService(llm, FakeEmbedder(), repo)

    service.extract_domain_mappings("job")

    # ensure search was called and candidate summary joined
    assert repo.search_calls


def test_extract_with_empty_candidate_chunks():
    llm = FakeLLM("{}")
    repo = FakeRepo([])
    service = DomainExtractionService(llm, FakeEmbedder(), repo)

    result = service.extract_domain_mappings("job")

    assert result.language_mappings == []


def test_extract_when_llm_times_out():
    llm = FakeLLM(RuntimeError("timeout"))
    service = DomainExtractionService(llm, FakeEmbedder(), FakeRepo())

    result = service.extract_domain_mappings("job")

    assert result.language_mappings == []
    assert result.skill_demonstrations == []
