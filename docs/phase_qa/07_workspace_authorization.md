# Developer Interview Q&A — Workspace Authorization

## 1. What invariant defines workspace authorization?

The backend derives a trusted principal, looks up that subject's memberships in PostgreSQL, and returns or accepts only workspace IDs in that authorized set. A client-provided workspace ID selects scope but never grants access.

## 2. Why does `workspace_id` remain text instead of becoming a UUID?

The existing ingestion, retrieval, pgvector metadata, configuration, and tests already use stable text IDs such as `local`. Authorization comes from membership validation, not from making identifiers difficult to guess.

## 3. How do local and office identities differ?

Local mode uses one fixed server-configured subject. Office mode reads identity headers injected only after gateway authentication. Both produce the same `Principal` object, so membership and application logic remain environment-neutral.

## 4. How is two-user isolation tested without browser-controlled identity?

Unit/API tests override FastAPI's principal dependency with Alice or Bob. They verify that one principal cannot discover unauthorized workspaces or load another principal's session, without adding an unsafe local identity-selection mechanism.

## 5. How is session-ID reuse protected?

Before reading conversation history, the store verifies that an existing session ID has the same owner and workspace. A mismatch is rejected, and session list/load/rename/archive operations are constrained by owner and workspace.

## 6. Why are migrations separate from application startup?

Versioned SQL gives schema changes a reviewable, repeatable deployment boundary. The runtime account does not need DDL privileges; startup only validates required tables, migration versions, and vector dimensions and fails clearly when deployment is incomplete.

## 7. What must the frontend do when workspace authorization changes?

It should refresh `GET /workspaces`, clear or replace an invalid selection, and handle `403` without retrying under an invented identity. It must never send a user ID; the backend always derives ownership itself.
