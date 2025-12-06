import random
import socket
from uuid import uuid4

import psycopg
import pytest
from pgvector.psycopg import register_vector

from rag_project.config import EMBEDDING_DIM, DOC_TYPE_JOB_POSTING
from rag_project.infrastructure.health import db_settings


def _socket_allowed(host: str, port: int) -> bool:
    try:
        s = socket.socket()
    except PermissionError:
        return False
    try:
        s.settimeout(1)
        s.connect((host, port))
        return True
    except PermissionError:
        return False
    except OSError:
        return True
    finally:
        s.close()


def test_pgvector_search_roundtrip():
    """Insert/query a single embedding to validate vector search and cascade cleanup."""
    settings = db_settings()
    host, port = settings["host"], int(settings["port"])
    if not _socket_allowed(host, port):
        pytest.skip("Socket connections are blocked in this environment.")

    doc_id = uuid4()
    chunk_id = uuid4()
    vector = [random.random() for _ in range(EMBEDDING_DIM)]
    delete_count = None
    try:
        with psycopg.connect(connect_timeout=60, **settings) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO documents (id, doc_type, created_at) VALUES (%s, %s, NOW())",
                    (doc_id, DOC_TYPE_JOB_POSTING),
                )
                cur.execute(
                    "INSERT INTO chunks (id, document_id, chunk_index, content) VALUES (%s, %s, %s, %s)",
                    (chunk_id, doc_id, 0, "vector test chunk"),
                )
                cur.execute(
                    "INSERT INTO embeddings (chunk_id, embedding) VALUES (%s, %s::vector)",
                    (chunk_id, vector),
                )
                cur.execute(
                    """
                    SELECT e.chunk_id
                    FROM embeddings e
                    JOIN chunks c ON c.id = e.chunk_id
                    WHERE c.document_id = %s
                    ORDER BY e.embedding <=> %s::vector
                    LIMIT 1
                    """,
                    (doc_id, vector),
                )
                nearest = cur.fetchone()
    except psycopg.OperationalError as exc:
        pytest.skip(f"Database not reachable: {exc}")
    finally:
        try:
            with psycopg.connect(connect_timeout=60, **settings) as conn:
                register_vector(conn)
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
                    delete_count = cur.rowcount
        except psycopg.OperationalError:
            pass

    assert (
        nearest is not None and nearest[0] == chunk_id
    ), "Inserted embedding was not retrieved as nearest"
    assert (
        delete_count == 1
    ), f"Cleanup did not delete inserted document {doc_id} (chunk {chunk_id}), delete_count={delete_count}"
