# Current Work Phase — NP-05 Workspace Discovery and Authorization

**Status:** Active  
**Last reviewed:** 2026-08-23  
**Owner:** Project team

## Objective

Define the authorized `workspace_id` source and backend contract that allow the frontend to present only workspaces available to the authenticated user and safely scope chat/session history.

## Current Blocker

The frontend architecture requires workspace selection, but the backend has no approved workspace discovery or authorization source. The frontend must not invent workspace options or submit a user identity to obtain them.

## Scope and Guardrails

- Derive identity from the trusted gateway/server-side development configuration; never accept a browser-supplied user ID.
- Define how an authenticated user receives their authorized workspaces.
- Define a workspace discovery API and its response contract before frontend implementation resumes.
- Apply the same authorization rule to chat, session, and recent-history operations.
- Preserve the existing default local-development workspace behavior until an approved replacement exists.
- Do not implement frontend UI, ingestion/admin features, or infrastructure deployment work in this phase.
- Do not start Uvicorn, models, pgvector, Langfuse, or office services without announcing it first.

## Task Board

| ID | Task | Status |
|---|---|---|
| CW-01 | Inspect current `workspace_id` lifecycle and identity handling. | Pending |
| CW-02 | Decide the authorization source: gateway claim/header, PostgreSQL membership records, or an approved local-development mapping. | Pending |
| CW-03 | Design the workspace discovery endpoint and response schema. | Pending |
| CW-04 | Define enforcement for workspace-scoped chat, session, and history operations. | Pending |
| CW-05 | Add focused unit tests and update frontend/backend documentation after the contract is approved. | Pending |
| CW-06 | Index the completed documentation and record the frontend handoff. | Pending |

## Approval Gates

- Approve the production authorization source and local-development fallback before adding an endpoint or persistence model.
- Review the workspace API contract before the frontend consumes it.
- Approve any database migration, gateway configuration, or live integration validation separately.

## Handoff Constraint

The frontend workspace selector remains blocked until CW-02 and CW-03 provide an approved authorized workspace source and API contract.
