\if :{?schema}
\else
\set schema rag
\endif

BEGIN;

CREATE TABLE IF NOT EXISTS :"schema".account_preferences (
    subject TEXT PRIMARY KEY,
    recent_chat_limit INTEGER NOT NULL DEFAULT 10
        CHECK (recent_chat_limit IN (10, 20, 50, 100)),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO :"schema".schema_migrations (version)
VALUES ('008_account_preferences') ON CONFLICT (version) DO NOTHING;

COMMIT;
