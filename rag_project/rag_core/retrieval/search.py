from typing import List

from rag_project.rag_core.domain.models import Citation, RAGAnswer, RetrievedChunk
from rag_project.rag_core.ports.embedding_port import EmbeddingProvider
from rag_project.rag_core.ports.llm_port import LLMProvider
from rag_project.rag_core.ports.repo_port import ChunkRepository
from rag_project.config import DEFAULT_MIN_MATCH_SCORE, DEFAULT_SEARCH_LIMIT, RETRIEVAL_SYSTEM_PROMPT, ANSWER_DEFAULT_TOP_K
from rag_project.logger import get_logger


logger = get_logger(__name__)


def vector_search(
    query: str,
    embedder: EmbeddingProvider,
    chunk_repo: ChunkRepository,
    limit: int = DEFAULT_SEARCH_LIMIT,
    min_match_score: float = DEFAULT_MIN_MATCH_SCORE,
    posted_after: float | None = None,
    doc_types: list[str] | None = None,
) -> List[RetrievedChunk]:
    logger.debug("Vector search start: query_len=%d limit=%d min_score=%.2f doc_types=%s", len(query), limit, min_match_score, doc_types)
    q_emb = embedder.embed([query])[0]
    results = chunk_repo.search(
        q_emb,
        limit=limit,
        min_match_score=min_match_score,
        posted_after=posted_after,
        doc_types=doc_types,
    )
    logger.info("Vector search returned %d chunks", len(results))
    return results


def build_prompt(question: str, retrieved: List[RetrievedChunk]) -> str:
    context_parts = []
    for rc in retrieved:
        meta = f"doc_type={rc.document.doc_type or 'unknown'}"
        title = None
        company = None
        url = None
        if rc.job_posting:
            title = rc.job_posting.title
            company = rc.job_posting.company
            url = rc.job_posting.url
        if title:
            meta += f" | title={title}"
        if company:
            meta += f" | company={company}"
        if url:
            meta += f" | url={url}"
        context_parts.append(f"[{meta}] {rc.chunk.content}")
    context = "\n\n".join(context_parts)
    return RETRIEVAL_SYSTEM_PROMPT.format(context=context, question=question)


def answer_question(
    question: str,
    embedder: EmbeddingProvider,
    llm: LLMProvider,
    chunk_repo: ChunkRepository,
    limit: int = ANSWER_DEFAULT_TOP_K,
    min_match_score: float = DEFAULT_MIN_MATCH_SCORE,
    posted_after: float | None = None,
    doc_types: list[str] | None = None,
) -> RAGAnswer:
    retrieved = vector_search(
        question,
        embedder,
        chunk_repo,
        limit=limit,
        min_match_score=min_match_score,
        posted_after=posted_after,
        doc_types=doc_types,
    )
    prompt = build_prompt(question, retrieved)
    logger.debug("Sending retrieval prompt to LLM with %d contexts", len(retrieved))
    response = llm.generate(prompt)
    citations = []
    for rc in retrieved:
        citations.append(
            Citation(
                chunk_id=rc.chunk.id,
                document_id=rc.document.id,
                score=rc.score,
                doc_type=rc.document.doc_type,
                url=rc.job_posting.url if rc.job_posting else None,
                title=rc.job_posting.title if rc.job_posting else None,
                company=rc.job_posting.company if rc.job_posting else None,
            )
        )
    return RAGAnswer(answer=response, citations=citations)
