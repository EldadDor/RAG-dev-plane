# Current Work Phase — NP-05 Workspace Discovery and Authorization

**Status:** Complete
**Last reviewed:** 2026-08-29
**Owner:** Project team

## Objective

Define the authorized `workspace_id` source and backend contract that allow the frontend to present only workspaces available to the authenticated user and safely scope chat/session history.

## Approved Resolution

Use the invariant `trusted identity -> PostgreSQL membership lookup -> authorized workspace IDs`.

- PostgreSQL is the authorization source in local and office environments.
- Office identity comes from a gateway-validated principal; local identity comes from fixed server-side configuration.
- The frontend discovers workspaces through `GET /workspaces`; it never invents workspace options or supplies a user ID.
- Every workspace-scoped operation revalidates membership through one reusable authorization dependency.
- Two-user isolation is tested with FastAPI dependency overrides. No browser-selectable or local identity-header override will be added.

## Scope and Guardrails

- Represent the authenticated identity with one environment-neutral principal abstraction.
- Derive office identity from trusted gateway headers and local identity from fixed server-side configuration; never accept a browser-supplied user ID.
- Store workspace membership in PostgreSQL under the configured schema (`rag` by default).
- Keep `workspace_id` as `TEXT` to preserve compatibility with ingestion, retrieval, pgvector metadata, tests, and `DEFAULT_WORKSPACE_ID=local`.
- Extend the existing `chat_sessions`, `conversation_turns`, and `conversation_summaries` model; do not introduce parallel session/message tables.
- Expose `GET /workspaces` using the existing application route style. An external Nginx `/api` prefix is a deployment concern.
- Apply the same authorization rule to chat, session, and recent-history operations.
- Constrain existing-session operations by session ID, workspace ID, and principal subject; reject ownership or workspace mismatches.
- Begin with constrained `owner` and `member` workspace roles. NP-05 authorizes both roles to use the workspace.
- Preserve the existing default local-development workspace behavior until an approved replacement exists.
- Do not implement frontend UI, ingestion/admin features, or infrastructure deployment work in this phase.
- Do not start Uvicorn, models, pgvector, Langfuse, or office services without announcing it first.

## Task Board

| ID | Task | Status |
|---|---|---|
| CW-01 | Inspect current `workspace_id` lifecycle and identity handling. | Complete |
| CW-02 | Approve PostgreSQL membership, gateway office identity, and fixed local identity. | Complete |
| CW-03 | Approve `GET /workspaces`, text workspace IDs, and the principal response contract. | Complete |
| CW-04 | Implement the principal abstraction, workspace membership persistence, and local seed behavior. | Complete |
| CW-05 | Implement discovery and centralized enforcement across chat and session operations. | Complete |
| CW-06 | Add focused unit tests, update documentation, index the result, and record the frontend handoff. | Complete 2026-08-29: canonical frontend JSON/error contract, focused tests, migrations/local seed, live PostgreSQL API validation, shared handoff, and documentation indexing completed. |

## Approval Gates

- Production authorization source, local identity behavior, and API contract were approved on 2026-08-24.
- Review schema changes and enforcement tests before closing NP-05.
- Approve any database migration, gateway configuration, or live integration validation separately.

## Handoff Constraint

The frontend design blocker is resolved. `GET /workspaces` and centralized
authorization are implemented and live-validated after applying the SQL
migrations and local seed. The frontend can run its approved local proxy
integration.

## Validation Evidence

- Python compilation completed successfully.
- Isolated suite: `47 passed, 1 skipped in 2.21s` on Python 3.14.
- Live validation completed against the configured PostgreSQL host: PostgreSQL
  16.14, pgvector 0.8.3, and migrations `001_baseline` and
  `002_workspace_authorization` are present.
- The configured FastAPI application successfully served health, workspace
  discovery, session list/detail, unauthorized-workspace, and unknown-session
  checks against PostgreSQL. No chat model, embedding model, or Langfuse
  service was contacted.
- After the embedding endpoint was restored, the idempotent documentation scan
  completed successfully. The `local` workspace contains 55 source-document
  records and 417 document chunks, including the shared agent-handoff records.

## Completion Record

NP-05 completed 2026-08-29. The frontend contract, authorization enforcement,
versioned migrations, local seed, live PostgreSQL validation, and indexed
documentation are complete. NP-06 remains the next queued phase.
