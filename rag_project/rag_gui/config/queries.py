"""SQL queries used by the GUI workers."""

GUI_JOBLOADER_QUERY = """
                        SELECT 
                            d.id, 
                            jp.title, 
                            jp.company, 
                            jp.location_text, 
                            d.created_at
                        FROM documents d
                        JOIN job_postings jp ON d.id = jp.document_id
                        WHERE d.doc_type = 'job_posting'
                        ORDER BY d.created_at DESC
                    """

GUI_CHUNK_COUNT_QUERY = """
                        SELECT d.doc_type, COUNT(c.id) 
                        FROM documents d 
                        LEFT JOIN chunks c ON c.document_id = d.id 
                        GROUP BY d.doc_type
                    """

GUI_DELETE_STATS_QUERIES = {
    "docs": "SELECT COUNT(*) FROM documents",
    "chunks": "SELECT COUNT(*) FROM chunks",
    "embeds": "SELECT COUNT(*) FROM embeddings",
}

GUI_DOC_LIST_QUERY_BASE = """
                        SELECT d.id, d.doc_type, d.created_at,
                               COALESCE(
                                   d.metadata->>'title',
                                   d.metadata->>'company',
                                   d.metadata->>'name',
                                   ''
                               ) AS label
                        FROM documents d
                    """
GUI_DOC_LIST_FILTER_QUERY = "WHERE d.doc_type = %s ORDER BY d.created_at DESC"

GUI_DB_SIZE_QUERY = "SELECT pg_database_size(current_database())"
GUI_DOC_COUNT_QUERY = "SELECT doc_type, COUNT(*) FROM documents GROUP BY doc_type"

__all__ = [
    "GUI_JOBLOADER_QUERY",
    "GUI_CHUNK_COUNT_QUERY",
    "GUI_DELETE_STATS_QUERIES",
    "GUI_DOC_LIST_QUERY_BASE",
    "GUI_DOC_LIST_FILTER_QUERY",
    "GUI_DB_SIZE_QUERY",
    "GUI_DOC_COUNT_QUERY",
]
