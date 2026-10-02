\if :{?schema}
\else
\set schema rag
\endif

BEGIN;

ALTER TABLE :"schema".document_index_metadata
    DROP CONSTRAINT IF EXISTS document_index_metadata_document_type_check;
ALTER TABLE :"schema".document_index_metadata
    ADD CONSTRAINT document_index_metadata_document_type_check
    CHECK (document_type IN
        ('word', 'powerpoint', 'pdf', 'markdown', 'html', 'text', 'code', 'unknown'));

INSERT INTO :"schema".schema_migrations (version)
VALUES ('007_powerpoint_document_type') ON CONFLICT (version) DO NOTHING;

COMMIT;
