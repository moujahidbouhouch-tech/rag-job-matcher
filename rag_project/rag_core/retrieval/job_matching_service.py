"""Job Matching Service

Orchestrates job-candidate matching:
1) Extract requirements from a job posting (LLM)
2) Search evidence for each requirement (vector search)
3) Evaluate evidence against each requirement (LLM)
"""

import json
import re
from typing import List

from rag_project.config import (
    DOC_TYPE_CV,
    DOC_TYPE_THESIS,
    DOC_TYPE_PERSONAL_PROJECT,
    JOB_MATCHING_EXTRACTION_MODEL,
    JOB_MATCHING_EVALUATOR_MODEL,
    JOB_MATCHING_SEARCH_LIMIT,
    JOB_MATCHING_MIN_MATCH_SCORE,
    JOB_MATCHING_EXTRACTION_MAX_TOKENS,
    JOB_MATCHING_EVALUATION_MAX_TOKENS,
    JOB_MATCHING_JOB_TEXT_LIMIT,
    JOB_MATCHING_EXTRACTION_PROMPT,
    JOB_MATCHING_EVALUATION_PROMPT,
)
from rag_project.config import DOMAIN_MAPPINGS, INFERENCE_RULES, CITATION_TOP_K
from rag_project.logger import get_logger
from rag_project.rag_core.domain.models import (
    JobRequirement,
    RequirementEvaluation,
    JobMatchResult,
)
from rag_project.rag_core.ports.embedding_port import EmbeddingProvider
from rag_project.rag_core.ports.llm_port import LLMProvider
from rag_project.rag_core.ports.repo_port import ChunkRepository
from rag_project.rag_core.retrieval.domain_extraction_service import DomainExtractionService, DomainMapping

logger = get_logger(__name__)


class JobMatchingService:
    """
    Repository + Service pattern:
    - Depends on ports (EmbeddingProvider, LLMProvider, ChunkRepository)
    - Stateless across calls
    """

    def __init__(
        self,
        embedder: EmbeddingProvider,
        llm: LLMProvider,
        chunk_repo: ChunkRepository,
        extraction_model: str = JOB_MATCHING_EXTRACTION_MODEL,
        evaluator_model: str = JOB_MATCHING_EVALUATOR_MODEL,
        search_limit: int = JOB_MATCHING_SEARCH_LIMIT,
        min_match_score: float = JOB_MATCHING_MIN_MATCH_SCORE,
        domain_extractor: DomainExtractionService | None = None,
    ) -> None:
        self.embedder = embedder
        self.llm = llm
        self.chunk_repo = chunk_repo
        self.extraction_model = extraction_model
        self.evaluator_model = evaluator_model
        self.search_limit = search_limit
        self.min_match_score = min_match_score
        self.domain_extractor = domain_extractor

    def analyze_match(self, job_text: str) -> JobMatchResult:
        """Analyze candidate match against a job posting."""
        logger.info("Job matching: starting extraction (model=%s)", self.extraction_model)

        domain_mappings = self.extract_domain_knowledge(job_text)
        requirements = self._extract_requirements(job_text)
        logger.info("Job matching: extracted %d requirements", len(requirements))

        if not requirements:
            return JobMatchResult(
                job_text=job_text,
                extracted_requirements=[],
                evaluations=[],
                match_count=0,
                missing_count=0,
                match_rate=0.0,
            )

        evaluations = []
        for idx, req in enumerate(requirements, 1):
            logger.debug("Job matching: evaluating %s (%d/%d)", req.name, idx, len(requirements))
            evaluations.append(self._evaluate_requirement(req, domain_mappings))

        match_count = sum(
            1 for e in evaluations if "MATCH" in e.verdict.upper() and "MISSING" not in e.verdict.upper()
        )
        missing_count = len(evaluations) - match_count
        match_rate = (match_count / len(evaluations) * 100) if evaluations else 0.0

        logger.info(
            "Job matching: completed %d/%d matches (%.1f%%)",
            match_count,
            len(evaluations),
            match_rate,
        )

        return JobMatchResult(
            job_text=job_text,
            extracted_requirements=requirements,
            evaluations=evaluations,
            match_count=match_count,
            missing_count=missing_count,
            match_rate=match_rate,
        )

    def _extract_requirements(self, job_text: str) -> List[JobRequirement]:
        """Extract requirements from job posting using an LLM."""
        limited_text = job_text[:JOB_MATCHING_JOB_TEXT_LIMIT]
        prompt = JOB_MATCHING_EXTRACTION_PROMPT.format(job_text=limited_text)

        try:
            response = self.llm.generate(
                prompt,
                model=self.extraction_model,
                max_tokens=JOB_MATCHING_EXTRACTION_MAX_TOKENS,
            )
            data = json.loads(self._clean_json(response))
            return [
                JobRequirement(
                    name=item.get("name", "").strip(),
                    category=item.get("category", "Hard Skill"),
                    search_query=item.get("search_query", "").strip(),
                    inference_rule=item.get("inference_rule", "").strip(),
                )
                for item in data.get("requirements", [])
                if item.get("name")
            ]
        except Exception as exc:  # noqa: BLE001
            logger.error("Job matching: extraction failed: %s", exc, exc_info=True)
            return []

    def _evaluate_requirement(self, req: JobRequirement, domain_mappings: DomainMapping | None = None) -> RequirementEvaluation:
        """Search evidence and evaluate a single requirement."""
        query_embedding = self.embedder.embed_query(req.search_query)
        chunks = self.chunk_repo.search(
            query_embedding=query_embedding,
            limit=self.search_limit,
            doc_types=[DOC_TYPE_CV, DOC_TYPE_THESIS, DOC_TYPE_PERSONAL_PROJECT],
            min_match_score=self.min_match_score,
        )

        evidence_lines = [f"- {rc.chunk.content[:500]}..." for rc in chunks]
        evidence_str = "\n".join(evidence_lines)

        if not chunks:
            return RequirementEvaluation(
                requirement=req,
                verdict="❌ MISSING",
                reasoning="No evidence found (no chunks retrieved)",
                retrieved_chunks_count=0,
                evidence_preview="",
                citations=[],
            )

        inference_rule = req.inference_rule or INFERENCE_RULES.get(req.category, "Apply strict keyword matching")

        language_mappings, skill_demonstrations, credential_mappings = self._format_domain_mappings(domain_mappings)

        prompt = JOB_MATCHING_EVALUATION_PROMPT.format(
            domain_mappings=DOMAIN_MAPPINGS,
            requirement_name=req.name,
            category=req.category,
            inference_rule=inference_rule,
            evidence=evidence_str,
            language_mappings=language_mappings,
            skill_demonstrations=skill_demonstrations,
            credential_mappings=credential_mappings,
        )

        try:
            response = self.llm.generate(
                prompt,
                model=self.evaluator_model,
                max_tokens=JOB_MATCHING_EVALUATION_MAX_TOKENS,
            )
            verdict_line = response.strip()
            parts = verdict_line.split("|", 1)
            status = parts[0].strip() if parts else "UNKNOWN"
            reasoning_raw = parts[1].strip() if len(parts) > 1 else verdict_line
            reasoning = reasoning_raw.splitlines()[0] if reasoning_raw else reasoning_raw

            citations = self._build_citations(chunks)
            return RequirementEvaluation(
                requirement=req,
                verdict=status,
                reasoning=reasoning,
                retrieved_chunks_count=len(chunks),
                evidence_preview=evidence_str[:200],
                citations=citations,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Job matching: evaluation failed for '%s': %s", req.name, exc)
            return RequirementEvaluation(
                requirement=req,
                verdict="ERROR",
                reasoning=f"Evaluation failed: {exc}",
                retrieved_chunks_count=len(chunks),
                evidence_preview=evidence_str[:200],
                citations=[],
            )

    def extract_domain_knowledge(self, job_text: str) -> DomainMapping | None:
        if not self.domain_extractor:
            return None
        try:
            return self.domain_extractor.extract_domain_mappings(job_text)
        except Exception as exc:  # noqa: BLE001
            logger.error("Job matching: domain extraction failed: %s", exc, exc_info=True)
            return DomainMapping(
                language_mappings=[],
                skill_demonstrations=[],
                credential_mappings=[],
            )

    @staticmethod
    def _format_domain_mappings(domain_mappings: DomainMapping | None) -> tuple[str, str, str]:
        if not domain_mappings:
            return ("none", "none", "none")

        def fmt_language():
            if not domain_mappings.language_mappings:
                return "none"
            lines = []
            for item in domain_mappings.language_mappings:
                src = item.get("source_term", "")
                eqs = ", ".join(item.get("equivalent_terms", []))
                ctx = item.get("context", "")
                lines.append(f"- {src} -> {eqs} ({ctx})")
            return "\n".join(lines)

        def fmt_skills():
            if not domain_mappings.skill_demonstrations:
                return "none"
            lines = []
            for item in domain_mappings.skill_demonstrations:
                task = item.get("task_description", "")
                skills = ", ".join(item.get("implied_skills", []))
                loc = item.get("evidence_location", "")
                lines.append(f"- {task} -> {skills} ({loc})")
            return "\n".join(lines)

        def fmt_credentials():
            if not domain_mappings.credential_mappings:
                return "none"
            lines = []
            for item in domain_mappings.credential_mappings:
                cred = item.get("candidate_credential", "")
                eqs = ", ".join(item.get("equivalent_to", []))
                reason = item.get("reasoning", "")
                lines.append(f"- {cred} -> {eqs} ({reason})")
            return "\n".join(lines)

        return fmt_language(), fmt_skills(), fmt_credentials()

    @staticmethod
    def _build_citations(chunks: list) -> list[dict]:
        cites = []
        for idx, rc in enumerate(chunks[:CITATION_TOP_K], start=1):
            cites.append(
                {
                    "label": idx,
                    "chunk_id": str(rc.chunk.id),
                    "doc_id": str(rc.document.id),
                    "doc_type": rc.document.doc_type,
                    "score": rc.score,
                    "content": rc.chunk.content,
                    "metadata": rc.document.metadata,
                    "title": getattr(rc.job_posting, "title", None) if rc.job_posting else None,
                    "company": getattr(rc.job_posting, "company", None) if rc.job_posting else None,
                }
            )
        return cites

    @staticmethod
    def _clean_json(text: str) -> str:
        """Remove markdown code fences from JSON response."""
        match = re.search(r"```(?:json)?\s*(.*)\s*```", text, re.DOTALL)
        if match:
            return match.group(1)
        return text.strip()
