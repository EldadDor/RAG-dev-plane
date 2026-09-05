\if :{?schema}
\else
\set schema rag
\endif

\if :{?table}
\else
\set table document_chunks
\endif

BEGIN;

-- Profiles isolate alternative chunking experiments. Existing source rows and
-- chunk metadata remain the `default` profile, preserving all current data.
ALTER TABLE :"schema".source_documents
    ADD COLUMN IF NOT EXISTS chunking_profile TEXT NOT NULL DEFAULT 'default';

ALTER TABLE :"schema".source_documents
    DROP CONSTRAINT IF EXISTS source_documents_pkey;

ALTER TABLE :"schema".source_documents
    ADD CONSTRAINT source_documents_pkey
    PRIMARY KEY (workspace_id, chunking_profile, doc_id);

DROP INDEX IF EXISTS :"schema".idx_rag_source_documents_root;
CREATE INDEX IF NOT EXISTS idx_rag_source_documents_profile_root
    ON :"schema".source_documents (workspace_id, chunking_profile, root_path);

-- Chunks are deliberately profile-scoped in JSONB so the vector table remains
-- compatible with the externally managed baseline schema.
UPDATE :"schema".:"table"
SET metadata = jsonb_set(metadata, '{chunking_profile}', '"default"'::jsonb, true)
WHERE NOT (metadata ? 'chunking_profile');

CREATE INDEX IF NOT EXISTS idx_rag_document_chunks_workspace_profile
    ON :"schema".:"table" ((metadata->>'workspace_id'), (metadata->>'chunking_profile'));

INSERT INTO :"schema".schema_migrations (version)
VALUES ('003_chunking_profiles')
ON CONFLICT (version) DO NOTHING;

COMMIT;
