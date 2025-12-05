# Configuration Guide

This project reads settings from environment variables with fallback defaults. Define them in `.env` or your process environment.

## Database (RAG)
- `POSTGRES_HOST_RAG` → `POSTGRES_HOST` → `DB_POSTGRESDB_HOST` → `DB_HOST` (default `localhost`)
- `POSTGRES_PORT_RAG` → `POSTGRES_PORT` → `DB_POSTGRESDB_PORT` → `DB_PORT` (default `5433`)
- `POSTGRES_DB_RAG` → `POSTGRES_DB` → `DB_POSTGRESDB_DATABASE` → `DB_NAME` (default `rag`)
- `POSTGRES_USER_RAG` → `POSTGRES_USER` → `DB_POSTGRESDB_USER` → `DB_USER` (default `rag`)
- `POSTGRES_PASSWORD_RAG` → `POSTGRES_PASSWORD` → `DB_POSTGRESDB_PASSWORD` → `DB_PASSWORD` (default empty)

### Tests
- When running pytest, DB settings are forced to `TEST_DB_HOST/PORT/NAME/USER/PASSWORD` (defaults: `127.0.0.1:5433`, `rag_test_db`, `rag`, empty password). Set these to a non-production DB.

## Ollama / LLM
- `OLLAMA_HOST` (default `http://127.0.0.1:11434`)
- `OLLAMA_MODEL` / `OLLAMA_FALLBACK_MODEL`
- `OLLAMA_NUM_CTX` (context window override for primary model)
- `OLLAMA_TIMEOUT` (seconds)
- `OLLAMA_HEALTHCHECK_PATH` (default `/api/tags`)
- `OLLAMA_HEALTH_TIMEOUT_SECONDS` (default `5`)
- `OLLAMA_MODELS` (space-separated list used by `scripts/ensure_services.sh` to pull models)

## Chunking / Embeddings
- `EMBEDDING_MODEL_ID` (default `BAAI/bge-m3`)
- `CHUNK_TOKEN_TARGET`, `CHUNK_OVERLAP_TOKENS`
- `USE_STRUCTURED_CHUNKER` (`1/0`)
- `STRUCTURED_USE_LLM` (`1/0`)
- `CHUNK_ASSIST_MODEL_ID`

## Job Matching
- `JOB_MATCHING_EXTRACTION_MODEL` (default `llama3.1:8b-instruct-q8_0`)
- `JOB_MATCHING_EVALUATOR_MODEL` (default `llama3.1:8b-instruct-q8_0`)

## GUI
- `GUI_DB_CHECK_TIMEOUT`, `GUI_JOBLOADER_DB_TIMEOUT` (optional; defaults in code)

## Logging
- `LOG_LEVEL` controls verbosity; file path/format are fixed defaults (`logs/rag.log`).
- `LOG_MAX_BYTES` (default 2000000) and `LOG_BACKUP_COUNT` (default 5) control rotating file handler size/retention.

## Example .env (RAG)
```
POSTGRES_HOST_RAG=localhost
POSTGRES_PORT_RAG=5433
POSTGRES_DB_RAG=rag
POSTGRES_USER_RAG=rag
POSTGRES_PASSWORD_RAG=secret

TEST_DB_HOST=127.0.0.1
TEST_DB_PORT=5433
TEST_DB_NAME=rag_test_db
TEST_DB_USER=rag
TEST_DB_PASSWORD=secret

OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b-instruct-q4_k_m
OLLAMA_FALLBACK_MODEL=llama3.1:8b
OLLAMA_MODELS="qwen2.5:7b-instruct-q4_k_m qwen2.5:1.5b-instruct llama3.1:8b"
OLLAMA_HEALTH_TIMEOUT_SECONDS=5

CHUNK_TOKEN_TARGET=512
CHUNK_OVERLAP_TOKENS=128
USE_STRUCTURED_CHUNKER=1
STRUCTURED_USE_LLM=0

JOB_MATCHING_EXTRACTION_MODEL=llama3.1:8b-instruct-q8_0
JOB_MATCHING_EVALUATOR_MODEL=llama3.1:8b-instruct-q8_0
```
