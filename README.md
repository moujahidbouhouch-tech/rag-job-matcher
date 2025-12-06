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
- Python 3.12.6+ (recommended: 3.12.10)
- **Visual C++ Redistributables** (Windows only - **CRITICAL for PyTorch**): [Download here](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- Ollama running locally with models pulled:
  - `qwen2.5:7b-instruct-q4_k_m` (primary + CV chunking)
  - `llama3.1:8b` (fallback)
  - `qwen2.5:1.5b-instruct` (chunking assist)
- Embeddings: `BAAI/bge-m3` (multilingual, 1024-d) for cross-language support.

## Quick Start
1. **Create and activate virtual environment** (Python 3.12.6+):
```bash
   python -m venv .venv

   # Windows (CMD)
   .venv\Scripts\activate.bat
   
   # Linux/macOS
   source .venv/bin/activate
```

2. **Install dependencies**:
```bash
   pip install -r requirements.txt
```

3. **Configure environment**:
```bash
   cp .env.example .env   # Edit DB credentials if needed
```

4. **Apply database schema**:
```bash
   # Linux/macOS
   ./scripts/apply_rag_schema.sh
   
   # Windows (using Docker)
   docker exec -i rag-db psql -U rag -d rag < scripts/rag_schema.sql
```

5. **Pull Ollama models** (see Prerequisites section)

6. **Start the GUI**:
```bash
   # Linux/macOS
   ./scripts/run_gui.sh
   
   # Windows
   .\scripts\run_gui.bat
   
   # Or manually
   python -m rag_project.rag_gui.main
```
   
   **Note:** For better PyQt performance, run the launch script from a separate terminal outside VSCode.

## GPU Support & PyTorch Configuration

### Overview
This application uses PyTorch for embeddings and can leverage GPU acceleration for significantly faster processing. The required PyTorch version depends on your hardware.

### Tested Configurations

| Hardware | PyTorch Version | CUDA | Embeddings | LLMs (Ollama) |
|----------|----------------|------|------------|---------------|
| CPU Only | 2.6.0 (CPU) | N/A | CPU | CPU |
| NVIDIA RTX 5060 Ti (sm_120) | 2.6.0 (CPU) | N/A | CPU | GPU |
| NVIDIA GPUs (sm_50 - sm_90) | 2.6.0 (cu124) | 12.4 | GPU | GPU |

### GPU Compatibility Check

If you encounter CUDA errors during embedding (e.g., "no kernel image is available for execution on the device"), check your GPU's compute capability:
```bash
python -c "import torch; print(torch.cuda.get_device_capability())"
```

**Note:** CUDA errors only affect embeddings. LLM inference via Ollama uses GPU independently and is unaffected.

**Common scenarios:**

1. **Compute capability ≤ 9.0** (older GPUs):
```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

2. **Compute capability ≥ 12.0** (RTX 50-series, Blackwell architecture):
```bash
   pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu126
```

3. **CPU-only** (no GPU or debugging):
```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Troubleshooting

**Error: "CUDA error: no kernel image is available"**
- Your GPU's compute capability is not supported by the installed PyTorch version
- Solution: Install nightly builds (see scenario 2 above)

**Error: "A dynamic link library (DLL) initialization routine failed"** (Windows)
- Missing Visual C++ Redistributables (see Prerequisites)
- Solution: Install from https://aka.ms/vs/17/release/vc_redist.x64.exe

**Slow performance during embedding:**
- Check if CUDA is enabled: `python -c "import torch; print(torch.cuda.is_available())"`
- If `False`, reinstall PyTorch with CUDA support (see above)

### Performance Notes
- **GPU acceleration**: Embeddings process ~10-50x faster than CPU when GPU-supported
- **RTX 50-series limitation**: Ollama LLMs use GPU normally; embeddings run on CPU until PyTorch adds sm_120 support
- **VRAM requirements**: Minimum 4GB recommended, 8GB+ for large documents
- **CPU fallback**: Always works but slower for embeddings only (LLM inference unaffected)


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