from uuid import uuid4

import psycopg
import pytest
from pgvector.psycopg import register_vector
from psycopg.types.json import Json
from rag_project.config import EMBEDDING_DIM

from rag_project.rag_core.config import get_settings
from rag_project.rag_core.domain.models import Chunk, Document, JobPosting
from rag_project.config import SUPPORTED_DOC_TYPES
from rag_project.rag_core.infra.db_pgvector import PgVectorRepository


def _dsn():
    settings = get_settings()
    pw = f" password={settings.db_password}" if settings.db_password else ""
    return (
        f"host={settings.db_host} "
        f"port={settings.db_port} "
        f"dbname={settings.db_name} "
        f"user={settings.db_user}"
        f"{pw}"
    )


def _repo():
    return PgVectorRepository(_dsn())


def _db_available():
    try:
        psycopg.connect(_dsn(), connect_timeout=120).close()
        return True
    except (psycopg.OperationalError, PermissionError) as exc:
        print(f"[debug:test_storage_service] DB not reachable: {exc}")
        return False


def _clear_tables():
    try:
        with psycopg.connect(_dsn(), connect_timeout=30) as conn, conn.cursor() as cur:
            register_vector(conn)
            cur.execute(
                'TRUNCATE "embeddings", "chunks", "job_postings", "personal_documents", "company_info", "documents" RESTART IDENTITY CASCADE'
            )
            conn.commit()
    except (psycopg.OperationalError, PermissionError) as exc:
        pytest.skip(f"Database not reachable for clear_tables: {exc}")


def _vector(val: float = 0.1):
    return [val for _ in range(EMBEDDING_DIM)]


def test_storage_insert_and_fetch_roundtrip():
    if not _db_available():
        pytest.skip("Database not reachable")
    repo = _repo()
    doc = Document(id=uuid4(), doc_type=SUPPORTED_DOC_TYPES[0])
    jp = JobPosting(document_id=doc.id, title="Doc 1")
    repo.insert_document(doc)
    repo.insert_job_posting(jp)
    chunk = Chunk(id=uuid4(), document_id=doc.id, chunk_index=0, content="hello world", token_count=2)
    repo.insert_chunks_with_embeddings([chunk], [_vector(0.1)])

    with psycopg.connect(_dsn(), connect_timeout=30) as conn, conn.cursor() as cur:
        register_vector(conn)
        cur.execute("SELECT doc_type FROM documents WHERE id = %s", (doc.id,))
        row = cur.fetchone()
    assert row == (doc.doc_type,)

    repo.delete_document(doc.id)


def test_storage_update_metadata_only():
    if not _db_available():
        pytest.skip("Database not reachable")
    repo = _repo()
    doc = Document(id=uuid4(), doc_type=SUPPORTED_DOC_TYPES[0], metadata={"initial": True})
    repo.insert_document(doc)

    with psycopg.connect(_dsn(), connect_timeout=30) as conn, conn.cursor() as cur:
        register_vector(conn)
        cur.execute("UPDATE documents SET metadata = %s WHERE id = %s", (Json({"updated": True}), doc.id))
        cur.execute("SELECT metadata FROM documents WHERE id = %s", (doc.id,))
        row = cur.fetchone()
    assert row and row[0]["updated"] is True

    repo.delete_document(doc.id)


def test_storage_delete_job_removes_embeddings():
    if not _db_available():
        pytest.skip("Database not reachable")
    repo = _repo()
    doc = Document(id=uuid4(), doc_type=SUPPORTED_DOC_TYPES[0])
    jp = JobPosting(document_id=doc.id, title="To delete")
    repo.insert_document(doc)
    repo.insert_job_posting(jp)
    chunk = Chunk(id=uuid4(), document_id=doc.id, chunk_index=0, content="bye", token_count=1)
    repo.insert_chunks_with_embeddings([chunk], [_vector(0.2)])

    repo.delete_document(doc.id)

    with psycopg.connect(_dsn(), connect_timeout=30) as conn, conn.cursor() as cur:
        register_vector(conn)
        cur.execute("SELECT 1 FROM embeddings WHERE chunk_id = %s", (chunk.id,))
        assert cur.fetchone() is None


def test_storage_rejects_duplicate_ids():
    if not _db_available():
        pytest.skip("Database not reachable")
    repo = _repo()
    doc = Document(id=uuid4(), doc_type=SUPPORTED_DOC_TYPES[0])
    repo.insert_document(doc)
    with pytest.raises(psycopg.Error):
        repo.insert_document(doc)
    repo.delete_document(doc.id)


def test_storage_handles_large_text_and_null_metadata():
    if not _db_available():
        pytest.skip("Database not reachable")
    repo = _repo()
    doc = Document(id=uuid4(), doc_type=SUPPORTED_DOC_TYPES[0], metadata=None)
    repo.insert_document(doc)
    large_content = "x" * 5000
    chunk = Chunk(id=uuid4(), document_id=doc.id, chunk_index=0, content=large_content, token_count=len(large_content.split()))
    repo.insert_chunks_with_embeddings([chunk], [_vector(0.05)])

    with psycopg.connect(_dsn(), connect_timeout=30) as conn, conn.cursor() as cur:
        register_vector(conn)
        cur.execute("SELECT LENGTH(content) FROM chunks WHERE id = %s", (chunk.id,))
        length = cur.fetchone()[0]
    assert length >= 5000

    repo.delete_document(doc.id)


def test_storage_vector_search_returns_nearest_neighbor():
    if not _db_available():
        pytest.skip("Database not reachable")
    _clear_tables()
    repo = _repo()
    doc_a = Document(id=uuid4(), doc_type=SUPPORTED_DOC_TYPES[0], metadata={"title": "A"})
    doc_b = Document(id=uuid4(), doc_type=SUPPORTED_DOC_TYPES[0], metadata={"title": "B"})
    repo.insert_document(doc_a)
    repo.insert_document(doc_b)
    repo.insert_job_posting(JobPosting(document_id=doc_a.id, title="A", match_score=0.9))
    repo.insert_job_posting(JobPosting(document_id=doc_b.id, title="B", match_score=0.1))
    chunk_a = Chunk(id=uuid4(), document_id=doc_a.id, chunk_index=0, content="doc a", token_count=2)
    chunk_b = Chunk(id=uuid4(), document_id=doc_b.id, chunk_index=0, content="doc b", token_count=2)
    repo.insert_chunks_with_embeddings([chunk_a, chunk_b], [_vector(0.9), _vector(0.1)])

    results = repo.search(query_embedding=_vector(0.9), limit=1)
    top_rc = results[0]
    assert top_rc.document.id == doc_a.id
    assert top_rc.chunk.id == chunk_a.id

    repo.delete_document(doc_a.id)
    repo.delete_document(doc_b.id)


def test_storage_schema_creation_allows_inserts():
    if not _db_available():
        pytest.skip("Database not reachable")
    repo = _repo()
    # If schema missing, this will raise; by inserting after ensuring table exists we validate migration scenario.
    doc = Document(id=uuid4(), doc_type=SUPPORTED_DOC_TYPES[0])
    repo.insert_document(doc)
    repo.delete_document(doc.id)
