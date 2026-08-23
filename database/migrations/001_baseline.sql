\if :{?schema}
\else
\set schema rag
\endif

\if :{?table}
\else
\set table document_chunks
\endif

\if :{?vector_dim}
\else
\set vector_dim 768
\endif

\if :{?embedding_index}
\else
\set embedding_index idx_rag_document_chunks_embedding_hnsw
\endif

\if :{?content_index}
\else
\set content_index idx_rag_document_chunks_content_fts
\endif

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS :"schema";

CREATE TABLE IF NOT EXISTS :"schema".schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS :"schema".:"table" (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(:vector_dim) NOT NULL,
    source VARCHAR(1000),
    page_number INTEGER,
    chunk_index INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS :"embedding_index"
    ON :"schema".:"table" USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS :"content_index"
    ON :"schema".:"table" USING gin (to_tsvector('simple', content));

CREATE TABLE IF NOT EXISTS :"schema".source_documents (
    doc_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    root_path TEXT,
    source_path TEXT NOT NULL,
    source_type TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, doc_id)
);

CREATE INDEX IF NOT EXISTS idx_rag_source_documents_root
    ON :"schema".source_documents (workspace_id, root_path);

CREATE TABLE IF NOT EXISTS :"schema".conversation_turns (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rag_conversation_turns_session_created
    ON :"schema".conversation_turns (session_id, created_at DESC, id DESC);

CREATE TABLE IF NOT EXISTS :"schema".conversation_summaries (
    session_id TEXT PRIMARY KEY,
    summary TEXT NOT NULL,
    last_turn_id BIGINT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS :"schema".chat_sessions (
    session_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    title TEXT NOT NULL,
    last_preview TEXT,
    archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rag_chat_sessions_owner_workspace
    ON :"schema".chat_sessions (owner_id, workspace_id, updated_at DESC)
    WHERE NOT archived;

INSERT INTO :"schema".schema_migrations (version)
VALUES ('001_baseline')
ON CONFLICT (version) DO NOTHING;

COMMIT;
