-- Provision one additive pgvector table for a registered embedding profile.
\if :{?schema}
\else
\set schema rag
\endif

\if :{?profile_name}
\else
\quit 'profile_name is required'
\endif

\if :{?model}
\else
\quit 'model is required'
\endif

\if :{?table}
\else
\quit 'table is required'
\endif

\if :{?vector_dim}
\else
\quit 'vector_dim is required'
\endif

BEGIN;

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

SELECT set_config('rag.profile_table', :'table', true),
       set_config('rag.profile_schema', :'schema', true);

DO $$
DECLARE
    target_table TEXT := current_setting('rag.profile_table');
    target_schema TEXT := current_setting('rag.profile_schema');
BEGIN
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS %I ON %I.%I USING hnsw (embedding vector_cosine_ops)',
        target_table || '_embedding_hnsw', target_schema, target_table
    );
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS %I ON %I.%I USING gin (to_tsvector(''simple'', content))',
        target_table || '_content_fts', target_schema, target_table
    );
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS %I ON %I.%I ((metadata->>''workspace_id''), (metadata->>''chunking_profile''))',
        target_table || '_workspace_chunking', target_schema, target_table
    );
END $$;

INSERT INTO :"schema".model_profiles
    (profile_name, provider, model, dimensions, storage_target, status)
VALUES (:'profile_name', 'ollama', :'model', :vector_dim, :'table', 'draft')
ON CONFLICT (profile_name) DO UPDATE SET
    provider = EXCLUDED.provider,
    model = EXCLUDED.model,
    dimensions = EXCLUDED.dimensions,
    storage_target = EXCLUDED.storage_target,
    status = CASE WHEN :"schema".model_profiles.status = 'ready' THEN 'ready' ELSE 'draft' END,
    updated_at = now();

COMMIT;
