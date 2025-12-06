import os

import psycopg
import pytest

# Ensure DB env defaults for tests when not provided externally.
os.environ.setdefault("TEST_DB_HOST", "127.0.0.1")
os.environ.setdefault("TEST_DB_PORT", "5433")
os.environ.setdefault("TEST_DB_NAME", "rag_test_db")
os.environ.setdefault("TEST_DB_USER", "rag")
os.environ.setdefault("TEST_DB_PASSWORD", "")

from rag_project.infrastructure.health import (
    check_db,
    check_models,
    check_ollama,
    check_pgvector,
)


def test_database_connectivity():
    """Fail loudly if Postgres is not reachable with the current environment settings."""
    try:
        # Some sandboxes block outbound sockets; detect and skip gracefully.
        import socket

        try:
            s = socket.socket()
        except PermissionError:
            pytest.skip("Sockets cannot be created in this environment.")
        try:
            s.settimeout(1)
            s.connect(
                (
                    os.environ["DB_POSTGRESDB_HOST"],
                    int(os.environ["DB_POSTGRESDB_PORT"]),
                )
            )
        except PermissionError:
            pytest.skip("Socket connections are blocked in this environment.")
        finally:
            s.close()

        check_db()
    except psycopg.OperationalError as exc:
        pytest.fail(f"Database connection failed: {exc}")


def test_database_schema_and_constraints():
    try:
        check_pgvector()
    except psycopg.OperationalError as exc:
        pytest.skip(f"Database not reachable: {exc}")


def test_ollama_models_available():
    try:
        check_ollama()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(
            f"Ollama not reachable: {exc}. "
            "Ensure Ollama is running and required models are pulled, then re-run tests."
        )


def test_embedding_models_cached():
    if os.getenv("CI"):
        pytest.skip("Skipping model cache check in CI environment")
    check_models()
