RAG System Overview
1. Purpose

This system provides a local Retrieval-Augmented Generation (RAG) pipeline designed to:

Fetch job postings or manual uploads

Process, embed, and store them locally

Enable semantic search, job matching, and Q&A

Run locally after models are pulled into Ollama / HF cache

Support English, German, and French

2. High-Level Architecture

The system is composed of:

Ingestion Pipeline

Collects job postings (or manual uploads)

Parses, chunks, embeds, stores, and extracts metadata via LLM

Query Pipeline

User interacts via GUI chat

Embeds queries, retrieves relevant chunks, ranks them, and generates answers

Job Matching Pipeline (invoked from GUI)

Extracts job requirements via LLM, searches candidate docs, and evaluates evidence per requirement

Local LLM + Embeddings

Embedding model: BGE-M3 (1024-d)

LLM: Qwen2.5 7B (primary, also CV chunker); fallback: Llama 3.1 8B; chunk-assist: Qwen2.5 1.5B

Vector Database

PostgreSQL + pgvector (default port 5433)

Stores documents, chunks, embeddings, and job metadata

3. Key Pipelines
3.1 Ingestion Pipeline (Overview)

Steps:

Parse and clean job text or uploaded file

Optional metadata extraction via LLM on text snippet

Chunk into overlapping segments (structured chunker profiles; CV uses LLM chunker)

Generate embeddings with BGE-M3

Store chunks + embeddings + metadata in PostgreSQL

Compute match_score (part of stored metadata/search scoring)

3.2 Query Pipeline (Overview)

Steps:

User submits a question via GUI chat

Embed query with BGE-M3

Perform pgvector similarity search

Score results (similarity + match_score + recency)

Build prompt with retrieved context

Generate answer via primary LLM

Return final answer + citations

3.3 Manual Upload Pipeline (Overview)

Steps:

User selects a file in the PyQt interface

File is parsed based on doc type

Same ingestion steps as above (parse → chunk → embed → store → score)

Status returned to UI

4. Technology Stack

Core

Python 3.12

BGE-M3 (embeddings, 1024-d)

Qwen2.5 7B primary LLM via Ollama; fallback Llama 3.1 8B; Qwen2.5 1.5B for chunk assist

PostgreSQL + pgvector

Interfaces

PyQt GUI (ingestion + chat + DB tooling)

5. Constraints & Design Requirements

Primary execution is local; models must be pulled into Ollama/HF cache first (network required once).

CPU-only assumed; ensure enough RAM for BGE-M3 and 7B model.

Multilingual (DE/EN/FR) targeted.

Modular and testable (ports + services).

Ingestion, Query, Manual Upload share the same core.

6. Folder Structure & Responsibilities

A detailed folder diagram and responsibility map is provided in:
📄 ~/documentation/folder_diagram_and_responsibility_map.md

Key notes:

rag_core contains domain logic, ports, and services (ingestion, retrieval, router, job matching, domain extraction)

rag_gui acts as the adapter; no CLI or HTTP API is present

infra provides implementations for DB, embeddings, and LLM

tests focus on ingestion/retrieval/job matching/GUI flows

## Usage
- Pull models into Ollama: `ollama pull qwen2.5:7b-instruct-q4_k_m`, `ollama pull qwen2.5:1.5b-instruct`, `ollama pull llama3.1:8b`.
- Start Postgres + pgvector (default port 5433, or set env vars).
- Launch GUI: `python -m rag_project.rag_gui.main`.
- Ingest documents (jobs, CVs, etc.) then query via chat or run job matching from the GUI.

## Operations
- Start dependencies: `./scripts/ensure_services.sh rag-postgres` (respects `POSTGRES_*_RAG` and `OLLAMA_*`).
- Apply schema: `./scripts/apply_rag_schema.sh`.
- Health checks: see `rag_project/infrastructure/health.py` for `check_db`, `check_pgvector`, `check_ollama`, `check_models`.

7. Diagrams

All sequence diagrams and intention diagrams are stored in:
📁 ~/documentation
📁 ~/documentation

Referenced in this overview for quick navigation.

8. Summary

This RAG system is designed to be:

Local-first

Modular and maintainable

Extensible (new sources, new models)

Reliable and testable

By separating ingestion, query, and manual upload flows—and implementing a clean architecture with clear roles—the system remains easy to understand, extend, and debug.
