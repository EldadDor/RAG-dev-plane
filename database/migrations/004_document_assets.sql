\if :{?schema}
\else
\set schema rag
\endif

BEGIN;

CREATE TABLE IF NOT EXISTS :"schema".document_assets (
    asset_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    chunking_profile TEXT NOT NULL,
    doc_id TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    media_type TEXT NOT NULL,
    byte_size BIGINT NOT NULL CHECK (byte_size >= 0),
    original_name TEXT,
    relationship_id TEXT,
    ordinal INTEGER NOT NULL,
    width INTEGER,
    height INTEGER,
    alt_text TEXT,
    caption TEXT,
    anchor_block_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (workspace_id, chunking_profile, doc_id)
        REFERENCES :"schema".source_documents (workspace_id, chunking_profile, doc_id)
        ON DELETE CASCADE,
    UNIQUE (workspace_id, chunking_profile, doc_id, asset_id)
);

CREATE INDEX IF NOT EXISTS idx_rag_document_assets_owner
    ON :"schema".document_assets (workspace_id, chunking_profile, doc_id, ordinal);

CREATE INDEX IF NOT EXISTS idx_rag_document_assets_storage_key
    ON :"schema".document_assets (storage_key);

CREATE TABLE IF NOT EXISTS :"schema".chunk_assets (
    workspace_id TEXT NOT NULL,
    chunking_profile TEXT NOT NULL,
    doc_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (workspace_id, chunking_profile, chunk_id, asset_id),
    FOREIGN KEY (workspace_id, chunking_profile, doc_id, asset_id)
        REFERENCES :"schema".document_assets
            (workspace_id, chunking_profile, doc_id, asset_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rag_chunk_assets_asset
    ON :"schema".chunk_assets (asset_id);

INSERT INTO :"schema".schema_migrations (version)
VALUES ('004_document_assets')
ON CONFLICT (version) DO NOTHING;

COMMIT;
