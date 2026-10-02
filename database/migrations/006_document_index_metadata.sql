\if :{?schema}
\else
\set schema rag
\endif

BEGIN;

CREATE TABLE IF NOT EXISTS :"schema".document_index_metadata (
    workspace_id TEXT NOT NULL REFERENCES :"schema".workspaces(workspace_id),
    model_profile TEXT NOT NULL REFERENCES :"schema".model_profiles(profile_name),
    chunking_profile TEXT NOT NULL,
    doc_id TEXT NOT NULL,
    title TEXT NOT NULL CHECK (char_length(title) BETWEEN 1 AND 300),
    file_name TEXT NOT NULL CHECK (char_length(file_name) BETWEEN 1 AND 255),
    document_type TEXT NOT NULL CHECK (document_type IN
        ('word', 'pdf', 'markdown', 'html', 'text', 'code', 'unknown')),
    content_hash TEXT,
    last_ingested_at TIMESTAMPTZ,
    indexed_chunk_count BIGINT NOT NULL CHECK
        (indexed_chunk_count BETWEEN 0 AND 9007199254740991),
    -- Private scan provenance, never included in the browser response.
    source_path TEXT NOT NULL,
    root_path TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (workspace_id, model_profile, chunking_profile, doc_id)
);

CREATE INDEX IF NOT EXISTS idx_document_index_metadata_recent
    ON :"schema".document_index_metadata
    (workspace_id, model_profile, chunking_profile,
     last_ingested_at DESC NULLS LAST, doc_id COLLATE "C" ASC);

-- A model publication owns references, while immutable asset metadata/bytes
-- may be shared by several profiles. Legacy chunk_assets remains compatible.
CREATE TABLE IF NOT EXISTS :"schema".document_index_assets (
    workspace_id TEXT NOT NULL,
    model_profile TEXT NOT NULL,
    chunking_profile TEXT NOT NULL,
    doc_id TEXT NOT NULL,
    asset_id TEXT NOT NULL REFERENCES :"schema".document_assets(asset_id) ON DELETE CASCADE,
    PRIMARY KEY (workspace_id, model_profile, chunking_profile, doc_id, asset_id),
    FOREIGN KEY (workspace_id, model_profile, chunking_profile, doc_id)
        REFERENCES :"schema".document_index_metadata
        (workspace_id, model_profile, chunking_profile, doc_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS :"schema".document_list_revisions (
    workspace_id TEXT NOT NULL REFERENCES :"schema".workspaces(workspace_id),
    model_profile TEXT NOT NULL REFERENCES :"schema".model_profiles(profile_name),
    chunking_profile TEXT NOT NULL,
    revision BIGINT NOT NULL DEFAULT 0 CHECK (revision >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (workspace_id, model_profile, chunking_profile)
);

-- Deployment-wide gate. Only an explicit successful operator reconciliation
-- enables the catalog. New ingestion alone cannot certify historical data.
CREATE TABLE IF NOT EXISTS :"schema".document_catalog_state (
    singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
    ready BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
INSERT INTO :"schema".document_catalog_state (singleton, ready)
VALUES (TRUE, FALSE) ON CONFLICT (singleton) DO NOTHING;

INSERT INTO :"schema".schema_migrations (version)
VALUES ('006_document_index_metadata') ON CONFLICT (version) DO NOTHING;

COMMIT;
