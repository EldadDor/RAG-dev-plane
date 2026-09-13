\if :{?schema}
\else
\set schema rag
\endif

\if :{?default_model}
\else
\set default_model nomic-embed-text
\endif

\if :{?default_dimensions}
\else
\set default_dimensions 768
\endif

\if :{?default_storage_target}
\else
\set default_storage_target document_chunks
\endif

BEGIN;

CREATE TABLE IF NOT EXISTS :"schema".model_profiles (
    profile_name TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    dimensions INTEGER NOT NULL CHECK (dimensions > 0),
    query_prefix TEXT NOT NULL DEFAULT '',
    document_prefix TEXT NOT NULL DEFAULT '',
    storage_target TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('draft', 'warming', 'ready', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS :"schema".embedding_cache (
    cache_key TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    dimensions INTEGER NOT NULL CHECK (dimensions > 0),
    embedding BYTEA NOT NULL,
    hit_count BIGINT NOT NULL DEFAULT 0 CHECK (hit_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_hit_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rag_embedding_cache_model
    ON :"schema".embedding_cache (provider, model, dimensions);

INSERT INTO :"schema".model_profiles
    (profile_name, provider, model, dimensions, storage_target, status)
VALUES ('default', 'ollama', :'default_model', :default_dimensions, :'default_storage_target', 'ready')
ON CONFLICT (profile_name) DO UPDATE SET
    provider = EXCLUDED.provider,
    model = EXCLUDED.model,
    dimensions = EXCLUDED.dimensions,
    storage_target = EXCLUDED.storage_target,
    updated_at = now();

INSERT INTO :"schema".schema_migrations (version)
VALUES ('005_model_profiles')
ON CONFLICT (version) DO NOTHING;

COMMIT;
