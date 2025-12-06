import math
import time
from typing import List, Optional, Dict, Any
from uuid import UUID

import psycopg
from psycopg.types.json import Json
from pgvector.psycopg import register_vector

from rag_project.config import (
    DB_CONNECT_TIMEOUT_SECONDS,
    DB_RETRY_ATTEMPTS,
    DB_RETRY_BACKOFF_SECONDS,
    DEFAULT_MIN_MATCH_SCORE,
    DEFAULT_SEARCH_LIMIT,
    RECENCY_DECAY_DAYS,
    WEIGHT_MATCH_SCORE,
    WEIGHT_RECENCY,
    WEIGHT_SIMILARITY,
    DOC_TYPE_JOB_POSTING,
    DOC_TYPE_CV,
    DOC_TYPE_COVER_LETTER,
    DOC_TYPE_THESIS,
    DOC_TYPE_PERSONAL_PROJECT,
    DOC_TYPE_COMPANY,
    SQL_INSERT_DOCUMENT,
    SQL_INSERT_JOB_POSTING,
    SQL_INSERT_PERSONAL_DOCUMENT,
    SQL_INSERT_COMPANY_INFO,
    SQL_DELETE_DOCUMENT,
    SQL_INSERT_CHUNK,
    SQL_INSERT_EMBEDDING,
    SQL_WHERE_MIN_MATCH,
    SQL_WHERE_POSTED_AFTER,
    SQL_WHERE_DOC_TYPES,
    SQL_WHERE_COMPANY_FILTER,
    SQL_VECTOR_SEARCH_QUERY,
)
from rag_project.logger import get_logger
from rag_project.rag_core.domain.models import (
    Chunk,
    CompanyInfo,
    Document,
    JobPosting,
    PersonalDocument,
    RetrievedChunk,
)
from rag_project.rag_core.ports.repo_port import ChunkRepository, DocumentRepository

logger = get_logger(__name__)


class PgVectorRepository(DocumentRepository, ChunkRepository):
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def _get_conn(self):
        conn = psycopg.connect(self.dsn, connect_timeout=DB_CONNECT_TIMEOUT_SECONDS)
        register_vector(conn)
        return conn

    # ------------------------------------------------------------------ #
    # Document/subtype inserts
    # ------------------------------------------------------------------ #
    def insert_document(self, document: Document) -> None:
        logger.debug(
            "repo.insert_document id=%s type=%s", document.id, document.doc_type
        )
        with self._get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                SQL_INSERT_DOCUMENT,
                (
                    document.id,
                    document.doc_type,
                    Json(document.metadata) if document.metadata else None,
                    document.created_at,
                ),
            )

    def insert_job_posting(self, job_posting: JobPosting) -> None:
        logger.debug(
            "repo.insert_job_posting doc_id=%s title=%s",
            job_posting.document_id,
            job_posting.title,
        )
        with self._get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                SQL_INSERT_JOB_POSTING,
                (
                    job_posting.document_id,
                    job_posting.related_company_id,
                    job_posting.title,
                    job_posting.location_text,
                    job_posting.salary_range,
                    job_posting.url,
                    job_posting.language,
                    job_posting.posted_at,
                    job_posting.match_score,
                    job_posting.company,
                ),
            )

    def insert_personal_document(self, personal: PersonalDocument) -> None:
        logger.debug(
            "repo.insert_personal_document doc_id=%s category=%s",
            personal.document_id,
            personal.category,
        )
        with self._get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                SQL_INSERT_PERSONAL_DOCUMENT,
                (personal.document_id, personal.category),
            )

    def insert_company_info(self, company: CompanyInfo) -> None:
        logger.debug(
            "repo.insert_company_info doc_id=%s name=%s",
            company.document_id,
            company.name,
        )
        with self._get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                SQL_INSERT_COMPANY_INFO,
                (company.document_id, company.name, company.industry),
            )

    def delete_document(self, document_id: UUID) -> None:
        logger.debug("repo.delete_document id=%s", document_id)
        with self._get_conn() as conn, conn.cursor() as cur:
            cur.execute(SQL_DELETE_DOCUMENT, (document_id,))

    # ------------------------------------------------------------------ #
    # Chunk + embedding
    # ------------------------------------------------------------------ #
    def insert_chunks_with_embeddings(
        self, chunks: List[Chunk], embeddings: List[List[float]]
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings length mismatch")
        logger.debug("repo.insert_chunks_with_embeddings count=%d", len(chunks))
        with self._get_conn() as conn, conn.cursor() as cur:
            for chunk, emb in zip(chunks, embeddings):
                cur.execute(
                    SQL_INSERT_CHUNK,
                    (
                        chunk.id,
                        chunk.document_id,
                        chunk.chunk_index,
                        chunk.content,
                        chunk.token_count,
                        chunk.created_at,
                    ),
                )
                cur.execute(
                    SQL_INSERT_EMBEDDING,
                    (chunk.id, emb),
                )

    # ------------------------------------------------------------------ #
    # Search
    # ------------------------------------------------------------------ #
    def _run_with_retry(self, func):
        last_exc = None
        for attempt in range(DB_RETRY_ATTEMPTS):
            try:
                return func()
            except psycopg.OperationalError as exc:
                last_exc = exc
                logger.warning(
                    "repo.search retry %d/%d: %s", attempt + 1, DB_RETRY_ATTEMPTS, exc
                )
                time.sleep(DB_RETRY_BACKOFF_SECONDS * (attempt + 1))
        if last_exc:
            logger.error("repo.search failed after retries: %s", last_exc)
            raise last_exc

    def search(
        self,
        query_embedding: List[float],
        limit: int = DEFAULT_SEARCH_LIMIT,
        min_match_score: float = DEFAULT_MIN_MATCH_SCORE,
        posted_after: float | None = None,
        doc_types: list[str] | None = None,
        filters: Dict[str, Any] | None = None,  # <--- ADDED ARGUMENT
    ) -> List[RetrievedChunk]:
        def _query():
            where_clauses = [SQL_WHERE_MIN_MATCH]
            params: list = [query_embedding, min_match_score]

            if posted_after is not None:
                where_clauses.append(SQL_WHERE_POSTED_AFTER)
                params.append(posted_after)

            if doc_types:
                where_clauses.append(SQL_WHERE_DOC_TYPES)
                params.append(doc_types)

            # --- NEW: Handle Filters (Company) ---
            if filters:
                if "company" in filters and filters["company"]:
                    # ILIKE for case-insensitive substring match on job_postings.company
                    where_clauses.append(SQL_WHERE_COMPANY_FILTER)
                    params.append(f"%{filters['company']}%")
            # -------------------------------------

            where_sql = " AND ".join(where_clauses)

            # Append the remaining params for ORDER BY and LIMIT
            params.extend([query_embedding, limit])

            sql = SQL_VECTOR_SEARCH_QUERY.format(
                where_sql=where_sql,
                WEIGHT_SIMILARITY=WEIGHT_SIMILARITY,
                WEIGHT_MATCH_SCORE=WEIGHT_MATCH_SCORE,
                WEIGHT_RECENCY=WEIGHT_RECENCY,
                RECENCY_DECAY_DAYS=RECENCY_DECAY_DAYS,
            )

            with self._get_conn() as conn, conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()

        rows = self._run_with_retry(_query)

        results: List[RetrievedChunk] = []
        for row in rows:
            (
                chunk_id,
                document_id,
                chunk_index,
                content,
                token_count,
                doc_id,
                doc_type,
                metadata,
                doc_created_at,
                title,
                company,
                location_text,
                language,
                url,
                posted_at,
                match_score,
                related_company_id,
                salary_range,
                personal_category,
                company_name,
                industry,
                distance,
                match_score_val,
                age_days,
            ) = row
            chunk = Chunk(
                id=chunk_id,
                document_id=document_id,
                chunk_index=chunk_index,
                content=content,
                token_count=token_count,
            )
            document = Document(
                id=doc_id,
                doc_type=doc_type,
                metadata=metadata,
                created_at=doc_created_at,
            )
            jp = None
            pd = None
            ci = None
            if doc_type == DOC_TYPE_JOB_POSTING:
                jp = JobPosting(
                    document_id=doc_id,
                    related_company_id=related_company_id,
                    title=title,
                    location_text=location_text,
                    salary_range=salary_range,
                    url=url,
                    language=language,
                    posted_at=posted_at,
                    match_score=match_score,
                    company=company,
                )
            if doc_type in {
                DOC_TYPE_CV,
                DOC_TYPE_COVER_LETTER,
                DOC_TYPE_THESIS,
                DOC_TYPE_PERSONAL_PROJECT,
            }:
                pd = PersonalDocument(
                    document_id=doc_id, category=personal_category or doc_type
                )
            if doc_type == DOC_TYPE_COMPANY:
                ci = CompanyInfo(
                    document_id=doc_id, name=company_name, industry=industry
                )

            similarity = 1 - float(distance)
            recency = (
                1.0
                if age_days is None
                else float(math.exp(-max(0.0, float(age_days)) / RECENCY_DECAY_DAYS))
            )
            score = (
                WEIGHT_SIMILARITY * similarity
                + WEIGHT_MATCH_SCORE * float(match_score_val)
                + WEIGHT_RECENCY * recency
            )
            results.append(
                RetrievedChunk(
                    chunk=chunk,
                    document=document,
                    score=score,
                    job_posting=jp,
                    personal=pd,
                    company_info=ci,
                )
            )
        return results
