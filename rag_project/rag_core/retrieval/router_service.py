"""Intent routing service for user messages."""

from dataclasses import dataclass
import json
from typing import Optional

from rag_project.config.prompts import ROUTER_SYSTEM_PROMPT
from rag_project.config import (
    ROUTER_HISTORY_CHAR_BUDGET,
    ROUTER_HISTORY_PER_MESSAGE_TRUNCATE,
)
from rag_project.rag_core.ports.llm_port import LLMProvider
from rag_project.logger import get_logger


logger = get_logger(__name__)


@dataclass
class RouteDecision:
    """Structured intent routing result."""

    action: str  # e.g., job_match | retrieve | help | unknown
    confidence: float = 1.0
    needs_clarification: bool = False
    clarification_prompt: Optional[str] = None
    extracted_params: Optional[dict] = None


class RouterService:
    """Classify user intent and decide which action to trigger."""

    def __init__(self, llm: LLMProvider):
        self._llm = llm

    def route(self, user_input: str, context: Optional[dict] = None) -> RouteDecision:
        """Run the router LLM and return a decision."""
        prompt = self._build_prompt(user_input, context or {})
        try:
            raw = self._llm.generate(prompt, max_tokens=256)
            decision = self._parse_response(raw)
            logger.info(
                "Router decision: action=%s confidence=%.2f needs_clarification=%s",
                decision.action,
                decision.confidence,
                decision.needs_clarification,
            )
            return decision
        except Exception as exc:
            logger.error("Router failed, returning unknown: %s", exc, exc_info=True)
            return RouteDecision(
                action="unknown",
                needs_clarification=True,
                clarification_prompt="I'm not sure what you'd like me to do. Could you clarify?",
            )

    def _build_prompt(self, user_input: str, context: dict) -> str:
        selected_jobs = context.get("selected_jobs") or []
        context_str = (
            f"Selected jobs: {len(selected_jobs)}"
            if selected_jobs
            else "Selected jobs: 0"
        )
        history = context.get("history") or []
        history_lines = []
        for msg in history:
            role = msg.get("role", "user")
            content = str(msg.get("content", ""))[:ROUTER_HISTORY_PER_MESSAGE_TRUNCATE]
            history_lines.append(f"{role}: {content}")
        history_block = "\n".join(history_lines)
        if len(history_block) > ROUTER_HISTORY_CHAR_BUDGET:
            history_block = history_block[-ROUTER_HISTORY_CHAR_BUDGET:]
        return ROUTER_SYSTEM_PROMPT.format(
            user_input=user_input,
            context=context_str + ("\n" + history_block if history_block else ""),
        )

    def _parse_response(self, response: str) -> RouteDecision:
        try:
            cleaned = response.strip().strip("`").strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
            data = json.loads(cleaned)
            return RouteDecision(
                action=data.get("action", "unknown"),
                confidence=data.get("confidence", 1.0),
                needs_clarification=data.get("needs_clarification", False),
                clarification_prompt=data.get("clarification"),
                extracted_params=data.get("params"),
            )
        except Exception:
            return RouteDecision(
                action="unknown",
                needs_clarification=True,
                clarification_prompt="I'm not sure what you'd like me to do. Could you clarify?",
            )
