from dataclasses import dataclass
import json
from typing import List, Dict, Any

from rag_project.config import (
    DOC_TYPE_CV,
    DOC_TYPE_THESIS,
    DOC_TYPE_PERSONAL_PROJECT,
    DOMAIN_MAPPING_EXTRACTION_PROMPT,
    DOMAIN_MAPPING_MAX_TOKENS,
    DOMAIN_MAPPING_CANDIDATE_LIMIT,
)
from rag_project.rag_core.ports.embedding_port import EmbeddingProvider
from rag_project.rag_core.ports.llm_port import LLMProvider
from rag_project.rag_core.ports.repo_port import ChunkRepository
from rag_project.logger import get_logger


logger = get_logger(__name__)


@dataclass
class DomainMapping:
    language_mappings: List[dict]
    skill_demonstrations: List[dict]
    credential_mappings: List[dict]


class DomainExtractionService:
    """Extract domain equivalences from job text and candidate documents."""

    def __init__(
        self, llm: LLMProvider, embedder: EmbeddingProvider, chunk_repo: ChunkRepository
    ):
        self.llm = llm
        self.embedder = embedder
        self.chunk_repo = chunk_repo

    def extract_domain_mappings(self, job_text: str) -> DomainMapping:
        candidate_summary = self._candidate_summary()
        logger.debug(
            "Domain extraction start: job_text_len=%d candidate_summary_len=%d",
            len(job_text),
            len(candidate_summary),
        )
        prompt = DOMAIN_MAPPING_EXTRACTION_PROMPT.format(
            job_text=job_text, candidate_summary=candidate_summary
        )
        try:
            raw = self.llm.generate(prompt, max_tokens=DOMAIN_MAPPING_MAX_TOKENS)
            cleaned = self._strip_code_fence(raw)
            data = json.loads(cleaned)
            logger.info(
                "Domain extraction succeeded with %d language mappings",
                len(data.get("language_mappings", [])),
            )
            return DomainMapping(
                language_mappings=data.get("language_mappings", []),
                skill_demonstrations=data.get("skill_demonstrations", []),
                credential_mappings=data.get("credential_mappings", []),
            )
        except Exception as exc:
            logger.error(
                "Domain extraction failed, returning empty mappings: %s",
                exc,
                exc_info=True,
            )
            # Fallback to empty mappings on any parse/LLM error
            return DomainMapping(
                language_mappings=[], skill_demonstrations=[], credential_mappings=[]
            )

    def _candidate_summary(self) -> str:
        query_embedding = self.embedder.embed(
            ["candidate profile education experience skills"]
        )[0]
        chunks = self.chunk_repo.search(
            query_embedding=query_embedding,
            limit=DOMAIN_MAPPING_CANDIDATE_LIMIT,
            doc_types=[DOC_TYPE_CV, DOC_TYPE_THESIS, DOC_TYPE_PERSONAL_PROJECT],
        )
        return "\n\n".join([rc.chunk.content for rc in chunks]) if chunks else ""

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        """Remove markdown code fences (```json ... ```), if present."""
        cleaned = text.strip()

        if cleaned.startswith("```"):
            newline_idx = cleaned.find("\n")
            if newline_idx != -1:
                cleaned = cleaned[newline_idx + 1 :]
            else:
                cleaned = cleaned[3:]

            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

        cleaned = cleaned.strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

        return cleaned
