"""SQL queries and health-check statements."""

SQL_INSERT_DOCUMENT = (
    "INSERT INTO documents (id, doc_type, metadata, created_at) VALUES (%s, %s, %s, %s)"
)
SQL_INSERT_JOB_POSTING = """
INSERT INTO job_postings
(document_id, related_company_id, title, location_text, salary_range, url, language, posted_at, match_score, company)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""
SQL_INSERT_PERSONAL_DOCUMENT = (
    "INSERT INTO personal_documents (document_id, category) VALUES (%s, %s)"
)
SQL_INSERT_COMPANY_INFO = (
    "INSERT INTO company_info (document_id, name, industry) VALUES (%s, %s, %s)"
)
SQL_DELETE_DOCUMENT = "DELETE FROM documents WHERE id = %s"
SQL_INSERT_CHUNK = "INSERT INTO chunks (id, document_id, chunk_index, content, token_count, created_at) VALUES (%s, %s, %s, %s, %s, %s)"
SQL_INSERT_EMBEDDING = "INSERT INTO embeddings (chunk_id, embedding, created_at) VALUES (%s, %s::vector, NOW())"
SQL_WHERE_MIN_MATCH = "COALESCE(jp.match_score, 0) >= %s"
SQL_WHERE_POSTED_AFTER = "jp.posted_at >= TO_TIMESTAMP(%s)"
SQL_WHERE_DOC_TYPES = "d.doc_type = ANY(%s)"
SQL_WHERE_COMPANY_FILTER = "jp.company ILIKE %s"
SQL_VECTOR_SEARCH_QUERY = """
                SELECT
                    c.id AS chunk_id,
                    c.document_id,
                    c.chunk_index,
                    c.content,
                    c.token_count,
                    d.id AS doc_id,
                    d.doc_type,
                    d.metadata,
                    d.created_at,
                    jp.title,
                    jp.company,
                    jp.location_text,
                    jp.language,
                    jp.url,
                    jp.posted_at,
                    jp.match_score,
                    jp.related_company_id,
                    jp.salary_range,
                    pd.category,
                    ci.name,
                    ci.industry,
                    (e.embedding <=> %s::vector) AS distance,
                    COALESCE(jp.match_score, 0) AS match_score,
                    EXTRACT(EPOCH FROM (NOW() - COALESCE(jp.posted_at, NOW()))) / 86400 AS age_days
                FROM embeddings e
                JOIN chunks c ON c.id = e.chunk_id
                JOIN documents d ON d.id = c.document_id
                LEFT JOIN job_postings jp ON jp.document_id = d.id
                LEFT JOIN personal_documents pd ON pd.document_id = d.id
                LEFT JOIN company_info ci ON ci.document_id = d.id
                WHERE {where_sql}
                ORDER BY ({WEIGHT_SIMILARITY} * (1 - (e.embedding <=> %s::vector))
                          + {WEIGHT_MATCH_SCORE} * COALESCE(jp.match_score, 0)
                          + {WEIGHT_RECENCY} * EXP(-GREATEST(0, COALESCE(EXTRACT(EPOCH FROM (NOW() - COALESCE(jp.posted_at, NOW()))) / 86400, 0)) / {RECENCY_DECAY_DAYS})) DESC
                LIMIT %s
            """

HEALTHCHECK_DB_PING_QUERY = "SELECT 1"
HEALTHCHECK_EXT_QUERY = "SELECT extname FROM pg_extension WHERE extname = ANY(%s)"
HEALTHCHECK_TABLE_QUERY = "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename = ANY(%s)"
HEALTHCHECK_INDEX_QUERY = "SELECT indexname FROM pg_indexes WHERE schemaname = 'public' AND indexname = ANY(%s)"
HEALTHCHECK_FK_QUERY = """
                SELECT
                    tc.table_name,
                    tc.constraint_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    rc.delete_rule
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                JOIN information_schema.referential_constraints AS rc
                    ON rc.constraint_name = tc.constraint_name
                    AND rc.constraint_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = 'public';
                """
HEALTHCHECK_COLUMN_QUERY = """
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND (table_name, column_name) IN (
                      SELECT table_name, column_name FROM (VALUES %s) AS t(table_name, column_name)
                  );
                """

SQL_FETCH_FULL_DOCUMENT = (
    "SELECT content FROM chunks WHERE document_id = %s ORDER BY chunk_index ASC"
)

__all__ = [
    "SQL_INSERT_DOCUMENT",
    "SQL_INSERT_JOB_POSTING",
    "SQL_INSERT_PERSONAL_DOCUMENT",
    "SQL_INSERT_COMPANY_INFO",
    "SQL_DELETE_DOCUMENT",
    "SQL_INSERT_CHUNK",
    "SQL_INSERT_EMBEDDING",
    "SQL_WHERE_MIN_MATCH",
    "SQL_WHERE_POSTED_AFTER",
    "SQL_WHERE_DOC_TYPES",
    "SQL_WHERE_COMPANY_FILTER",
    "SQL_VECTOR_SEARCH_QUERY",
    "HEALTHCHECK_DB_PING_QUERY",
    "HEALTHCHECK_EXT_QUERY",
    "HEALTHCHECK_TABLE_QUERY",
    "HEALTHCHECK_INDEX_QUERY",
    "HEALTHCHECK_FK_QUERY",
    "HEALTHCHECK_COLUMN_QUERY",
    "SQL_FETCH_FULL_DOCUMENT",
]
