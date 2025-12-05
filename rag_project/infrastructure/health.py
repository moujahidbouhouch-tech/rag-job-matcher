import os
from pathlib import Path
from typing import Dict

import httpx
import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from rag_project.logger import get_logger

from rag_project.config import (
    DB_CONNECT_TIMEOUT_SECONDS,
    DB_DEFAULT_HOST,
    DB_DEFAULT_NAME,
    DB_DEFAULT_PASSWORD,
    DB_DEFAULT_PORT,
    DB_DEFAULT_USER,
    HF_CACHE_DEFAULT_PATH,
    OLLAMA_DEFAULT_HOST,
    OLLAMA_HEALTHCHECK_PATH,
    OLLAMA_HEALTH_TIMEOUT_SECONDS,
    REQUIRED_COLUMNS,
    REQUIRED_EMBEDDING_MODELS,
    REQUIRED_EXTENSIONS,
    REQUIRED_FKS,
    REQUIRED_INDEXES,
    REQUIRED_LLM_MODELS,
    REQUIRED_TABLES,
    HEALTHCHECK_DB_PING_QUERY,
    HEALTHCHECK_EXT_QUERY,
    HEALTHCHECK_TABLE_QUERY,
    HEALTHCHECK_INDEX_QUERY,
    HEALTHCHECK_FK_QUERY,
    HEALTHCHECK_COLUMN_QUERY,
)

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=False)
HF_HOME = Path(os.getenv("HF_HOME", HF_CACHE_DEFAULT_PATH)).resolve()
logger = get_logger(__name__)


def db_settings() -> Dict[str, str]:
    """Collect DB settings from environment with sensible defaults for local docker-compose."""
    host = (
        os.getenv("DB_HOST")
        or os.getenv("DB_POSTGRESDB_HOST")
        or os.getenv("POSTGRES_HOST")
        or DB_DEFAULT_HOST
    )
    if host == "postgres":
        host = "localhost"
    port = (
        os.getenv("DB_PORT")
        or os.getenv("DB_POSTGRESDB_PORT")
        or os.getenv("POSTGRES_PORT")
        or str(DB_DEFAULT_PORT)
    )
    dbname = (
        os.getenv("DB_NAME")
        or os.getenv("DB_POSTGRESDB_DATABASE")
        or os.getenv("POSTGRES_DB")
        or DB_DEFAULT_NAME
    )
    user = (
        os.getenv("DB_USER")
        or os.getenv("DB_POSTGRESDB_USER")
        or os.getenv("POSTGRES_USER")
        or DB_DEFAULT_USER
    )
    password = (
        os.getenv("DB_PASSWORD")
        or os.getenv("DB_POSTGRESDB_PASSWORD")
        or os.getenv("POSTGRES_PASSWORD")
        or DB_DEFAULT_PASSWORD
    )
    return {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
    }


def ollama_base_url() -> str:
    host = os.getenv("OLLAMA_HOST", OLLAMA_DEFAULT_HOST)
    if not host.startswith("http"):
        host = f"http://{host}"
    return host


def embedding_cache_dirs() -> Dict[str, Path]:
    """Map required embedding model IDs to expected cache directories."""
    cache_dirs: Dict[str, Path] = {}
    for model_id in REQUIRED_EMBEDDING_MODELS:
        parts = model_id.split("/")
        if len(parts) != 2:
            continue
        org, name = parts
        cache_dirs[model_id] = HF_HOME / "hub" / f"models--{org}--{name}"
    return cache_dirs


def check_db() -> None:
    """Fail loudly if Postgres is not reachable."""
    logger.info("Healthcheck: checking database connectivity")
    settings = db_settings()
    redacted = {**settings, "password": "***"}
    with psycopg.connect(connect_timeout=DB_CONNECT_TIMEOUT_SECONDS, **settings) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(HEALTHCHECK_DB_PING_QUERY)
            result = cur.fetchone()
            if result != (1,):
                raise RuntimeError(f"Database connectivity check failed using settings {redacted}")
    logger.info("Healthcheck: database reachable")


def check_pgvector() -> None:
    """Ensure pgvector schema pieces (extensions, tables, indexes, constraints, columns) are present."""
    logger.info("Healthcheck: verifying pgvector schema elements")
    settings = db_settings()
    with psycopg.connect(connect_timeout=DB_CONNECT_TIMEOUT_SECONDS, **settings) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(HEALTHCHECK_EXT_QUERY, (list(REQUIRED_EXTENSIONS),))
            extensions = {row[0] for row in cur.fetchall()}
            cur.execute(HEALTHCHECK_TABLE_QUERY, (list(REQUIRED_TABLES),))
            tables = {row[0] for row in cur.fetchall()}
            cur.execute(HEALTHCHECK_INDEX_QUERY, (list(REQUIRED_INDEXES),))
            indexes = {row[0] for row in cur.fetchall()}

            cur.execute(HEALTHCHECK_FK_QUERY)
            fks = {
                (
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                )
                for row in cur.fetchall()
            }
            cur.execute(
                HEALTHCHECK_COLUMN_QUERY
                % ",".join([f"('{t}','{c}')" for (t, c) in REQUIRED_COLUMNS])
            )
            columns = {(row[0], row[1]) for row in cur.fetchall()}

    missing_extensions = REQUIRED_EXTENSIONS - extensions
    missing_tables = REQUIRED_TABLES - tables
    missing_indexes = REQUIRED_INDEXES - indexes
    missing_fks = REQUIRED_FKS - fks
    missing_columns = REQUIRED_COLUMNS - columns

    if missing_extensions:
        raise RuntimeError(f"Missing extensions: {sorted(missing_extensions)}")
    if missing_tables:
        raise RuntimeError(f"Missing tables: {sorted(missing_tables)}")
    if missing_indexes:
        raise RuntimeError(f"Missing indexes: {sorted(missing_indexes)}")
    if missing_columns:
        raise RuntimeError(f"Missing columns: {sorted(missing_columns)}")
    if missing_fks:
        raise RuntimeError(f"Missing foreign keys: {sorted(missing_fks)}")
    logger.info("Healthcheck: pgvector schema OK")


def check_ollama() -> None:
    """Ensure Ollama is reachable and required LLM models are present."""
    logger.info("Healthcheck: checking Ollama availability")
    base_url = ollama_base_url()
    resp = httpx.get(f"{base_url}{OLLAMA_HEALTHCHECK_PATH}", timeout=OLLAMA_HEALTH_TIMEOUT_SECONDS)
    resp.raise_for_status()
    data = resp.json()
    names = {model.get("name") for model in data.get("models", []) if model.get("name")}
    missing = REQUIRED_LLM_MODELS - names
    if missing:
        raise RuntimeError(f"Missing Ollama models: {sorted(missing)}")
    logger.info("Healthcheck: Ollama models present")


def check_models() -> None:
    """Ensure required embedding models are available locally (HF cache)."""
    logger.info("Healthcheck: checking embedding model cache dirs")
    cache_dirs = embedding_cache_dirs()
    missing = {mid for mid, path in cache_dirs.items() if not path.exists()}
    if missing:
        raise RuntimeError(f"Missing embedding model cache directories: {sorted(missing)}")
    logger.info("Healthcheck: embedding model cache present")
