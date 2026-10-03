\if :{?schema}
\else
\set schema rag
\endif

BEGIN;

-- Gateway owns these records. Payloads are encrypted outside PostgreSQL;
-- identifiers are hashes, never raw cookies or provider tokens.
CREATE TABLE IF NOT EXISTS :"schema".auth_sessions (
    token_hash TEXT PRIMARY KEY CHECK (token_hash ~ '^[0-9a-f]{64}$'),
    kind TEXT NOT NULL CHECK (kind IN ('session', 'bootstrap', 'login')),
    payload TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT false,
    CHECK (expires_at > created_at),
    CHECK (last_seen >= created_at)
);
CREATE INDEX IF NOT EXISTS auth_sessions_expiry_idx ON :"schema".auth_sessions (expires_at);

INSERT INTO :"schema".schema_migrations (version)
VALUES ('009_auth_sessions') ON CONFLICT (version) DO NOTHING;

COMMIT;
