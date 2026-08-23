\if :{?schema}
\else
\set schema rag
\endif

BEGIN;

CREATE TABLE IF NOT EXISTS :"schema".workspaces (
    workspace_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS :"schema".workspace_members (
    workspace_id TEXT NOT NULL
        REFERENCES :"schema".workspaces(workspace_id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member'
        CHECK (role IN ('owner', 'member')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, subject)
);

CREATE INDEX IF NOT EXISTS idx_workspace_members_subject
    ON :"schema".workspace_members (subject, workspace_id);

-- Adopt workspaces already present in document/session data before NP-05.
INSERT INTO :"schema".workspaces (workspace_id, display_name)
SELECT DISTINCT workspace_id, workspace_id
FROM :"schema".source_documents
ON CONFLICT (workspace_id) DO NOTHING;

INSERT INTO :"schema".workspaces (workspace_id, display_name)
SELECT DISTINCT workspace_id, workspace_id
FROM :"schema".chat_sessions
ON CONFLICT (workspace_id) DO NOTHING;

INSERT INTO :"schema".schema_migrations (version)
VALUES ('002_workspace_authorization')
ON CONFLICT (version) DO NOTHING;

COMMIT;
