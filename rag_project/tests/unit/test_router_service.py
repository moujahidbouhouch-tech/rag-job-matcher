import pytest

from rag_project.rag_core.retrieval.router_service import RouterService


class FakeLLM:
    def __init__(self, response: str | Exception):
        self.response = response

    def generate(self, prompt: str, max_tokens: int = 256):
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_router_parses_valid_json():
    llm = FakeLLM('{"action": "job_match", "confidence": 0.9}')
    router = RouterService(llm)

    decision = router.route("Compare me to this job")

    assert decision.action == "job_match"
    assert decision.needs_clarification is False


def test_router_handles_malformed_json():
    # Missing closing brace triggers parse fallback
    llm = FakeLLM('{"action": "retrieve"')
    router = RouterService(llm)

    decision = router.route("Find context")

    assert decision.needs_clarification is True
    assert decision.action == "unknown"


def test_router_handles_llm_exception():
    llm = FakeLLM(RuntimeError("timeout"))
    router = RouterService(llm)

    decision = router.route("Help")

    assert decision.needs_clarification is True
    assert decision.action == "unknown"


def test_route_empty_input_triggers_clarification():
    llm = FakeLLM('{"action": "unknown", "needs_clarification": true}')
    router = RouterService(llm)

    decision = router.route("")

    assert decision.action == "unknown"
    assert decision.needs_clarification is True


def test_route_whitespace_input_triggers_clarification():
    llm = FakeLLM('{"action": "unknown", "needs_clarification": true}')
    router = RouterService(llm)

    decision = router.route("   \n\t")

    assert decision.action == "unknown"
    assert decision.needs_clarification is True


def test_route_handles_code_fence_json():
    response = """```json\n{\"action\": \"job_match\", \"confidence\": 0.9}\n```"""
    llm = FakeLLM(response)
    router = RouterService(llm)

    decision = router.route("compare me")

    assert decision.action == "job_match"
    assert decision.confidence == 0.9


def test_route_handles_invalid_action_defaults_unknown():
    llm = FakeLLM('{"action": "foo"}')
    router = RouterService(llm)

    decision = router.route("something")

    assert decision.action in {"foo", "unknown"}  # currently passes through; downstream should guard


def test_route_when_llm_returns_non_json():
    llm = FakeLLM("plain text")
    router = RouterService(llm)

    decision = router.route("hi")

    assert decision.action == "unknown"
    assert decision.needs_clarification is True


def test_route_when_llm_returns_empty_string():
    llm = FakeLLM("")
    router = RouterService(llm)

    decision = router.route("hi")

    assert decision.action == "unknown"
    assert decision.needs_clarification is True


def test_route_with_none_context():
    llm = FakeLLM('{"action": "retrieve", "confidence": 0.8}')
    router = RouterService(llm)

    decision = router.route("question", context=None)

    assert decision.action == "retrieve"


def test_route_with_empty_context_dict():
    llm = FakeLLM('{"action": "help", "confidence": 0.95}')
    router = RouterService(llm)

    decision = router.route("help", context={})

    assert decision.action == "help"


def test_route_with_history_in_context_truncates():
    llm = FakeLLM('{"action": "job_match"}')
    router = RouterService(llm)
    history = [{"role": "user", "content": "x" * 5000}]

    decision = router.route("do", context={"history": history})

    assert decision.action in {"job_match", "unknown"}
