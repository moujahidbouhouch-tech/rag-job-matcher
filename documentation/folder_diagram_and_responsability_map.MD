## 1️⃣ Folder Diagram

```text
rag_project/
├─ rag_core/                      # Core logic (domain + ports + services)
│  ├─ config.py                   # AppSettings/env loading
│  ├─ domain/                     # Domain models & value objects
│  ├─ ports/                      # Embedding, LLM, repository interfaces
│  ├─ ingestion/                  # Parsing, chunking, ingestion service
│  ├─ retrieval/                  # Search, query service, router, job matching, domain extraction
│  ├─ infra/                      # PgVector repo, BGE-M3 embedder, Ollama LLM provider
│  └─ app_facade.py               # RAGApp wiring (repo/embedder/LLM + services)
├─ rag_gui/                       # PyQt GUI (ingestion, chat, DB stats/delete + workers/views)
└─ tests/                         # Pytest (unit + integration for ingestion/retrieval/job matching/GUI)
```

## 2️⃣ Responsibility Map

### Core (`rag_core/`)

| Module / Folder                            | Responsibility |
| ------------------------------------------ | -------------- |
| `config.py`                                | Loads settings from env; defaults for DB/Ollama/chunking. |
| `domain/models.py`, `domain/value_objects.py` | Domain entities (Document, Chunk, JobPosting, RAGAnswer, etc.). |
| `ports/*.py`                               | Interfaces for embedding, LLM, repositories. |
| `ingestion/parser.py`                      | Parse job/file inputs. |
| `ingestion/structured_chunker.py`, `ingestion/chunker.py`, `ingestion/cv_chunker.py` | Structured chunking (per doc-type profiles), CV LLM chunker. |
| `ingestion/service.py`                     | Orchestrates parse → metadata extraction via LLM → chunk → embed → store. |
| `retrieval/search.py`, `retrieval/service.py` | Vector search + prompt build + answer generation. |
| `retrieval/router_service.py`              | Intent routing for chat. |
| `retrieval/domain_extraction_service.py`   | Domain mapping extraction from job + candidate docs. |
| `retrieval/job_matching_service.py`        | Requirement extraction + evidence search + evaluation. |
| `infra/db_pgvector.py`                     | Pgvector repository; scoring combines similarity + match_score + recency. |
| `infra/embedding_bgem3.py`                 | BGE-M3 embedding provider. |
| `infra/llm_ollama.py`                      | Ollama-backed LLM provider. |
| `app_facade.py`                            | Wires providers/services into `RAGApp`. |

### Adapters

| Package | Responsibility |
| ------- | -------------- |
| `rag_gui/main.py` + `rag_gui/views/` + `rag_gui/workers/` | PyQt GUI: ingestion tab, RAG chat with job selection, DB stats, delete; background workers for ingestion/retrieval/job matching/router. |

No HTTP API is present (adapter removed).

### Tests (`rag_project/tests/`)

Contains unit and integration coverage for ingestion, retrieval, job matching, router, infra round-trips, GUI ingestion/query, and DB safety checks (`test_db_isolation.py`).
