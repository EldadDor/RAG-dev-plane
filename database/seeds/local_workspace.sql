\if :{?schema}
\else
\set schema rag
\endif

\if :{?default_workspace_id}
\else
\set default_workspace_id local
\endif

\if :{?local_subject}
\else
\set local_subject local-dev
\endif

BEGIN;

INSERT INTO :"schema".workspaces (workspace_id, display_name)
VALUES (:'default_workspace_id', 'Local Workspace')
ON CONFLICT (workspace_id) DO NOTHING;

INSERT INTO :"schema".workspace_members (workspace_id, subject, role)
VALUES (:'default_workspace_id', :'local_subject', 'owner')
ON CONFLICT (workspace_id, subject) DO NOTHING;

COMMIT;
