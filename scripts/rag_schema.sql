-- RAG schema for documents-centric storage
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    doc_type TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS company_info (
    document_id UUID PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    name TEXT,
    industry TEXT
);

CREATE TABLE IF NOT EXISTS job_postings (
    document_id UUID PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    related_company_id UUID REFERENCES company_info(document_id) ON DELETE SET NULL,
    title TEXT,
    location_text TEXT,
    salary_range TEXT,
    url TEXT,
    language TEXT,
    posted_at TIMESTAMPTZ,
    match_score DOUBLE PRECISION,
    company TEXT
);

CREATE TABLE IF NOT EXISTS personal_documents (
    document_id UUID PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    category TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    content TEXT NOT NULL,
    token_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS embeddings (
    chunk_id UUID PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
    embedding VECTOR(1024),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_job_postings_posted_at ON job_postings(posted_at);
CREATE INDEX IF NOT EXISTS idx_job_postings_match_score ON job_postings(match_score);
CREATE INDEX IF NOT EXISTS idx_embeddings_embedding_cosine ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
