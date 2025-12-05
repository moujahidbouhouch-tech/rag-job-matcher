# RAG Matching Workspace

Licensed under GNU AGPL-3.0 (see LICENSE file)

Local-first, privacy-centric RAG for intelligent document analysis and job matching. This is not a simple chat wrapper: it runs an extract → retrieve → evaluate pipeline to break down job requirements, fetch evidence from candidate documents, and produce verdicts with reasoning before surfacing results.

Module paths such as `rag_project/...` refer to the Python package in this repository. Run all commands from the project root.

## Key Features
- Local and private: runs on your machine using Ollama and PostgreSQL/pgvector.
- Three-stage job matching: requirement extraction → evidence retrieval → verdict/reasoning to avoid “lost in the middle”.
- Smart retrieval: similarity + match_score + recency scoring with pgvector IVFFLAT indexes.
- Structured chunking: per-doc-type strategies (CVs vs job descriptions), with optional LLM-assisted chunking.
- Full PyQt GUI for ingestion, chat, job matching, database overview, and deletes.
- Health checks for DB schema/pgvector/Ollama/models and strong pytest coverage (unit, integration, DB safety, GUI workers).

## Prerequisites
- Python 3.12
- PostgreSQL with pgvector enabled (default port 5433 for the RAG database)
- Ollama running locally with models pulled:
  - `qwen2.5:7b-instruct-q4_k_m` (primary + CV chunking)
  - `llama3.1:8b` (fallback)
  - `qwen2.5:1.5b-instruct` (chunking assist)
- Embeddings: `BAAI/bge-m3` (multilingual, 1024-d) for cross-language support.

## Quick Start
```bash
pip install -r requirements.txt
cp .env.example .env   # Edit DB credentials if needed
./scripts/apply_rag_schema.sh   # or: psql -f scripts/rag_schema.sql against the RAG database
python -m rag_project.rag_gui.main
```

## Configuration (environment variables)
Key variables (defaults come from the core config modules):

| Purpose | Env vars (first found wins) | Default |
| --- | --- | --- |
| RAG DB host/port | `DB_POSTGRESDB_HOST` / `POSTGRES_HOST_RAG` / `POSTGRES_HOST` / `DB_HOST`; `DB_POSTGRESDB_PORT` / `POSTGRES_PORT_RAG` / `POSTGRES_PORT` | `localhost`, `5433` |
| RAG DB name/user/pass | `DB_POSTGRESDB_DATABASE` / `POSTGRES_DB_RAG` / `POSTGRES_DB` / `DB_NAME`; `DB_POSTGRESDB_USER` / `POSTGRES_USER_RAG` / `POSTGRES_USER` / `DB_USER`; `DB_POSTGRESDB_PASSWORD` / `POSTGRES_PASSWORD_RAG` / `POSTGRES_PASSWORD` / `DB_PASSWORD` | `rag`, `rag`, empty password |
| Ollama endpoint/models | `OLLAMA_HOST`, `OLLAMA_MODEL`, `OLLAMA_FALLBACK_MODEL` | `http://127.0.0.1:11434`, `qwen2.5:7b-instruct-q4_k_m`, `llama3.1:8b` |
| Embeddings | `EMBEDDING_MODEL_ID` | `BAAI/bge-m3` (1024-d) |
| Chunking | `CHUNK_TOKEN_TARGET`, `CHUNK_OVERLAP_TOKENS`, `USE_STRUCTURED_CHUNKER`, `STRUCTURED_USE_LLM` | ~450-word target, ~90 overlap, structured chunker on, LLM assist off |

## Usage Notes
- docker-compose: set `OLLAMA_HOST=http://ollama:11434` and DB host to `rag-postgres`; on host, use `http://127.0.0.1:11434` and `localhost:5433`.
- Pull models before first run:
  ```bash
  ollama pull qwen2.5:7b-instruct-q4_k_m
  ollama pull qwen2.5:1.5b-instruct
  ollama pull llama3.1:8b
  ```
- Ensure PostgreSQL with pgvector is running on port 5433 (or adjust env vars). Start the GUI, ingest documents (jobs, CVs, etc.), then use chat or job matching.

## GUI Workflow
- Ingestion view (Ingest & Index): select/drop files, choose doc type, ingest → parse → chunk → embed → store in pgvector.
- Chat view (RAG): pick job postings, ask questions; retrieval uses similarity + match_score + recency and LLMs for answers.
- Job Matching view: requirement extraction → evidence retrieval per requirement → LLM evaluation with verdict/reasoning.
- Database view: document/chunk counts by type; reflects current DB connection.
- Delete view: load and delete documents from the current DB.

## Architecture & Logic
- Core wiring: `rag_project/rag_core/app_facade.py`
- Ingestion: `rag_project/rag_core/ingestion/service.py` (parsing, optional metadata extraction, structured chunking, embeddings)
- Retrieval: `rag_project/rag_core/retrieval/search.py` (scoring, retrieval, prompt construction, answer generation)
- Supporting components: job matching (`job_matching_service.py`), domain extraction, router, health checks (`infrastructure/health.py`)

## Job Matching Pattern (extract → retrieve → evaluate)
- Extract structured requirements from the job text with an LLM.
- Retrieve evidence chunks per requirement from the vector store (similarity + match_score + recency).
- Evaluate each requirement with LLM verdict/reasoning and surface signals to the GUI.
- Benefits over single-step semantic match: explainability (why matched), precision (avoid “lost in the middle” by isolating requirements).

## Documentation
- System/folder overviews: `documentation/rag_system_overview.MD`, `documentation/folder_diagram_and_responsability_map.MD`
- Diagrams: `documentation/intention_diagrams/`, `documentation/sequence_diagrams/`

## Status Notes
- Only the PyQt GUI adapter is included; no HTTP API is shipped in this repo.
- Older placeholder modules (`normalizer.py`, `scoring.py`, `query_builder.py`) are not present.

## Operations & Health
- Start dependencies: `./scripts/ensure_services.sh rag-postgres`
- Apply DB schema: `./scripts/apply_rag_schema.sh`
- Health checks (all at once): `python -m rag_project.infrastructure.health`

## Roadmap & Known Limitations
* **Performance:** Document ingestion and embedding are currently serial/synchronous. Large file ingestion may temporarily freeze the GUI or hit timeout limits.
* **Tokenization:** Chunking currently uses a word-count approximation logic rather than exact tokenizer counting.
* **Architecture:** Core services (Ollama, pgvector) are currently tightly coupled. Future updates will introduce stricter dependency injection and connection pooling.
* **Interface:** This is strictly a desktop application (PyQt). No CLI or Web API is currently exposed.