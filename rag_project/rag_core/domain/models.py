from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import List, Optional
from uuid import UUID, uuid4

from rag_project.config import DEFAULT_QUERY_TOP_K


@dataclass
class Document:
    id: UUID = field(default_factory=uuid4)
    doc_type: str = ""
    metadata: Optional[dict] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyInfo:
    document_id: UUID
    name: Optional[str] = None
    industry: Optional[str] = None


@dataclass
class JobPosting:
    document_id: UUID
    related_company_id: Optional[UUID] = None
    title: Optional[str] = None
    location_text: Optional[str] = None
    salary_range: Optional[str] = None
    url: Optional[str] = None
    language: Optional[str] = None
    posted_at: Optional[datetime] = None
    match_score: Optional[float] = None
    company: Optional[str] = None


@dataclass
class PersonalDocument:
    document_id: UUID
    category: Optional[str] = None  # cv, cover_letter, thesis, personal_project


@dataclass
class Chunk:
    id: UUID = field(default_factory=uuid4)
    document_id: UUID = field(default_factory=uuid4)
    chunk_index: int = 0
    content: str = ""
    token_count: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Optional[dict] = field(default_factory=dict)


@dataclass
class Query:
    text: str
    top_k: int = DEFAULT_QUERY_TOP_K


@dataclass
class RetrievedChunk:
    chunk: Chunk
    document: Document
    score: float
    job_posting: Optional[JobPosting] = None
    personal: Optional[PersonalDocument] = None
    company_info: Optional[CompanyInfo] = None


@dataclass
class Citation:
    chunk_id: UUID
    document_id: UUID
    score: float
    doc_type: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None


@dataclass
class RAGAnswer:
    answer: str
    citations: List[Citation]


# Job Matching Domain Models
@dataclass
class JobRequirement:
    """A single requirement extracted from a job posting."""

    name: str
    category: str  # "Hard Skill" | "Soft Skill" | "Implicit Trait"
    search_query: str
    inference_rule: str


@dataclass
class RequirementEvaluation:
    """Evaluation result for one requirement against candidate evidence."""

    requirement: JobRequirement
    verdict: str  # "✅ MATCH" | "⚠️ PARTIAL" | "❌ MISSING" | "ERROR"
    reasoning: str
    retrieved_chunks_count: int
    evidence_preview: str
    citations: list | None = None


@dataclass
class JobMatchResult:
    """Complete job matching analysis result."""

    job_text: str
    extracted_requirements: List[JobRequirement]
    evaluations: List[RequirementEvaluation]
    match_count: int
    missing_count: int
    match_rate: float  # percentage
