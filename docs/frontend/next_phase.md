# Next Frontend Phase — Approval Backlog

**Status:** FP-02 Frontend Hardening and UX Refinement is complete. This file
tracks work after FP-02; authoritative current-task status remains in
`work_current_phase.md`.
**Last reviewed:** 2026-10-03
**Owner:** Frontend team

## Current Phase Checkpoint

- FP-07 was activated on 2026-09-13 for the user-requested Vite multi-app
  project-layout migration; it is tracked in `work_current_phase.md`.
- FP-08 was activated on 2026-09-14 for individually collapsible source
  citations in the frontend Sources panel; it is tracked in
  `work_current_phase.md`.

- FP-01 received formal closure approval on 2026-09-05 after unit tests, type
  checks, and the production build passed.
- FP-02 was activated on 2026-09-05 with user approval for its accessibility,
  responsive behavior, recovery-state, and focused unit-test scope.
- FP-02 received formal closure approval on 2026-09-05 after the approved
  local validation set passed.
- FP-04 workspace selection and session list/load/new-chat flow completed on
  2026-08-29 against the approved API and error contracts.
- FP-05 bounded history, rename, and approved archive behavior completed on
  2026-08-29.
- FP-06 streaming, citations, cancellation, and recovery work completed and
  passed operator-run browser/API validation on 2026-09-03 through the IPv4
  Vite proxy with the live LLM and pgvector stack.
- Backend live-stack workspace/session validation and documentation indexing
  are complete; NP-05 is closed.
- The 2026-09-10 backend handoff confirms image-bearing source citations are
  implemented and contract-authoritative. The frontend implementation and
  focused parser coverage are present. The separately approved live
  Word/image browser checklist passed on 2026-09-12; NP-15-FE is complete.
- Hebrew and multilingual RAG evaluation is a backend-owned proposed NP-16
  requirement. Its requested evaluation and profile-isolation design were
  recorded in `../agent_handoff/frontend_to_backend.md` on 2026-09-12; it does
  not activate frontend work without a browser-visible contract or results UI.

This file is the frontend-only intake and ordering record. Before a candidate
becomes active, move it into `work_current_phase.md`, define its task board,
and record the applicable approval decision.

## Candidate Work

| Priority | ID | Candidate task | Why it matters | Approval required |
| --- | --- | --- | --- | --- |
| 1 | FP-03 | Office delivery integration | Configure the approved static deployment, proxy, identity handling, and SSE behavior with the infrastructure owner. | Gateway identity, Nginx/CI-CD/TLS/CORS, and deployment plan. |
| 2 | NP-15-FE | Image-bearing source citations | Render authorized images associated with retrieved Word citations in the Sources experience. | **Complete — live browser validated 2026-09-12** |

## Recommended Next Phase

FP-03 remains the existing delivery candidate. The NP-15 frontend slice
completed live browser validation on 2026-09-12.

## Phase Intake Checklist

- [x] Clear objective, bounded scope, and explicit exclusions.
- [x] Affected frontend files, dependencies, proxy behavior, and tests identified.
- [x] Backend-contract dependencies checked against `../frontend_architecture.md`.
- [x] Local validation defined; live validation requires separate approval.
- [x] Privacy, identity, and browser-secret exposure reviewed.
- [x] Required approvals and user/product decisions recorded.
- [x] Completion criteria and planned commit boundary recorded.

## Deferred Until Approved

- Gateway identity-header names and authentication implementation.
- Nginx CI/CD, static asset path, backend upstream, TLS, and CORS changes.
- Archive-versus-permanent-deletion wording.
- Ingestion, administration, provider, database, or backend contract changes.
- Image-bearing citation UI until NP-13 through NP-15 and the contract in
  `../document_image_support_plan.md` are approved.

## UI Enhancement Intake — 2026-10-02

FP-09 intake: record the requested recent-document panel, configurable chunk-size indicators, and document-type colors. Intake moved to the current task board; FP-10 through FP-12 are now implemented and locally validated in the current task board.

### FP-10 — Recent ingested documents panel

- Repurpose the left panel for a read-only recent-document list scoped to the selected authorized workspace. Preserve workspace selection and existing chat navigation.
- Show document title/name, document type, successful ingestion timestamp, and chunk count; order newest successful ingestion first with a stable tie-breaker.
- Make all recent documents reachable through bounded pagination or load-more behavior; define the time window/page size with the backend contract rather than silently truncating the list.
- Include loading, empty, error/retry, and refresh states. Clear stale records immediately on workspace changes; handle long names, Hebrew/RTL content, narrow layouts, keyboard access, and screen-reader labels.
- Completion: authorized metadata renders correctly, pagination and workspace switching work, and the list makes new information easy to identify. Selecting a document must not silently restrict retrieval; document-scoped querying requires a separately agreed contract and interaction.
- Dependency: backend publishes a workspace-authorized document-list route and metadata schema in `../frontend_architecture.md`. This is discovery of ingested content, not an ingestion/admin UI.

### FP-11 — Chunk counts and size colors

- Display the exact indexed chunk count alongside one of: Small, Medium, Big, Extra-Large.
- Keep ordered numeric thresholds and category colors in a single typed frontend configuration; no settings screen or new dependency is required for initial delivery.
- Choose and record default thresholds during implementation after backend count semantics are defined. Cover boundary counts, zero, and missing/unknown counts; unknown counts must not appear as zero or Small.
- Use readable text labels and accessible contrast so category meaning does not depend on color. Keep the size badge separate from the document-type badge.
- Completion: threshold/color edits need no component changes; focused unit checks verify classification boundaries and missing values.

### FP-12 — Document-type colors

- Display a text type label and separate type badge; map canonical types to colors in one typed frontend configuration.
- Provide a neutral Unknown/Other fallback for absent or unrecognized types. Do not infer canonical type solely from a filename extension unless the approved contract specifies that behavior.
- Use consistent mappings across the list, readable contrast, and a compact legend or equivalent explanation when needed.
- Completion: different supported types have distinguishable configured badges; fallback and size/type coexistence are verified.

### Delivery and validation

- Scope: existing frontend application components, styles, API adapter/types, and focused unit coverage. Identify exact files when activating each task; no application files changed during intake.
- Order: backend metadata contract, FP-10, FP-11, then FP-12. Move each candidate to `work_current_phase.md` before implementation.
- Planned commit boundaries: one reviewable commit per feature, prefixed with its task ID.
- On implementation, run permitted frontend type checks, focused tests, production build, and diff whitespace checks. Browser automation, new dependencies, and live model/database services retain their separate approval gates.
- Intake completed on 2026-10-02. No type checks, tests, builds, browser automation, or live services ran for this documentation-only task.

## UI Enhancement Activation — 2026-10-02

FP-10 through FP-12 moved to work_current_phase.md on user instruction to proceed after reviewing the implemented and live-validated NP-20 handoff. Acceptance criteria above remain applicable. Local unit/type/build checks are in scope; live browser validation remains separate.

## UI Enhancement Completion — 2026-10-02

FP-10, FP-11 and FP-12 completed implementation and local validation (34 unit
tests, type checks, production build, whitespace check). Metadata dependency
resolved by the newest NP-20 handoff. Defaults: Small 0–25, Medium 26–100,
Big 101–500, Extra-Large 501+ chunks; thresholds and type/size color pairs live
in `frontend/apps/rag-dev-plane/src/documentBadges.ts`.
Manual browser integration is unverified and requires the separately approved
live validation scope; no live services or browser automation ran.

## UI behavior intake activation — 2026-10-03

FP-13 (record UI behavior requirements and backend API handoff) moved to the current task board before intake work. This request authorizes planning and handoff only; FP-14 through FP-17 implementation remains backlog work.

## UI Behavior Requirements — 2026-10-03

Planning authorized by the user; implementation has not started. FP-13 records
this intake and its backend handoff. Move each candidate to the current board
before implementation. Existing FP-03 delivery work remains separate.

| Priority | ID | Candidate task | Dependency / readiness |
| --- | --- | --- | --- |
| 1 | FP-14 | Reliable New chat action with active-chat confirmation | Existing session/SSE contract; define active-chat predicate below in implementation. |
| 2 | FP-15 | Unique recent chats with selectable display limit | Existing session list; backend clarification requested if bounded server retrieval is needed. |
| 3 | FP-16 | Profile, Settings, and Logout actions | Backend account/preferences/authentication contract and product scope required. |
| 4 | FP-17 | Recent-document action menu, overview, and single-page preview | Backend authorized overview/preview capability contract required. |

### FP-14 — New chat always starts a fresh conversation

- Keep New chat actionable in every UI state: existing or empty chat, loading,
  streaming, interrupted/error states, and open rename/dialog/panel states.
- Prompt for approval only when in the middle of a chat. Proposed operational
  definition: an in-flight answer or unsent non-empty draft; merely viewing a
  completed conversation does not require confirmation. Record this definition
  when activating; clarify if product intent also includes completed sessions.
- Confirm continues to a fresh empty composer; Cancel preserves the draft,
  conversation, and running request. Prevent duplicate confirmation dialogs.
- On continuation, abort pending chat/detail requests and ignore stale results;
  clear active session, draft, turns, summary, citations, partial answer, errors,
  and transient chat actions. Preserve workspace and recent-chat navigation.
  Omit session_id on the first submitted turn; do not create empty server chats
  merely by clicking New chat. With no authorized workspace, still show the
  fresh-chat state and normal workspace selection requirement for submission.
- Do not delete/archive existing chats; honor documented cancellation persistence.
  Focus the composer and support keyboard/dialog focus behavior.
- Acceptance: state-matrix checks cover empty/completed/draft/loading/streaming/
  failed chat, confirm/cancel, repeated clicks, and late response suppression.

### FP-15 — Unique, bounded recent-chat list

- Investigate the reported duplicates before assigning a cause. Each item must
  represent a session, not a retrieved chunk, turn, or prompt-query result.
- Deduplicate by stable session_id within the authorized workspace; merge
  refreshed/session-completion data consistently and keep the newest updated_at
  record. Similar titles/previews with different IDs remain distinct chats.
- Default to the 10 most recently updated unique sessions. Place a labelled
  selector above the list with exactly 10, 20, 50, and 100 options; cap visible
  rows at the selected value after deduplication and newest-first sorting, with
  a stable session-ID tie-breaker. Keep the selected count during the current
  UI session; cross-login persistence depends on FP-16's settings contract.
- Changing the cap must not delete history or disrupt the active conversation;
  an active chat outside the cap remains open. Clear old workspace records,
  ignore stale responses, and preserve loading/empty/error/retry behavior.
- Acceptance: duplicate IDs, legitimately similar chats, refreshed records,
  timestamp ties, each cap, fewer-than-cap records, and workspace switching.
  If the server list is bounded, obtain enough unique sessions through an
  agreed limit/pagination contract; do not invent query parameters.

### FP-16 — Profile / Settings / Logout

- Proposed product scope: Profile shows the authenticated display name and
  backend-approved account/workspace details; Settings exposes supported user
  preferences (initial candidate: recent-chat cap); Logout ends the applicable
  authenticated session and returns to the documented signed-out experience.
- Treat this as a proposal requiring backend capability definitions, not a
  promise of editable identity, account administration, or provider settings.
  Publish which fields are read-only/editable and which preferences are local
  versus server-persisted before implementing controls.
- Menus/dialogs need keyboard access, focus return, save/cancel/error/loading
  states, and explicit unsupported capability handling. Never simulate successful
  logout by just hiding the chat; document fixed local-development identity behavior.
- Confirm interruption if logout would discard a draft or active answer. On
  successful logout, abort requests and clear protected sessions, documents,
  content and account data; block late responses from restoring signed-out data.
- Acceptance: supported/unsupported capabilities, preference validation and
  persistence, safe auth failures, logout success/failure, and stale-response guards.
- Dependency: 2026-10-03 frontend-to-backend handoff and published authoritative
  API contract, including gateway/identity-provider ownership of logout.

### FP-17 — Recent-document actions

- Add a clickable per-document action control to the left recent-documents panel
  with at least Brief overview and View document when supported. Use explicit
  capability/unavailable messages for unsupported actions; no guessed content URLs.
- Brief overview opens a clearly labelled overview of the selected whole document,
  not an arbitrary retrieved chunk. Show source identity and generation/provenance
  information supplied by the contract; handle loading/retry/empty/unavailable states.
- For a document with exactly one page (PDF/DOCX) or one slide (presentation),
  View document shows the complete authorized page/slide. DOCX page count must
  come from an agreed rendering, not chunk count or filename inference.
- Multi-page documents may show an overview and an explicit preview limitation;
  broader multipage viewing/download/navigation is a separate scope decision.
  Closing actions returns focus; support Hebrew/RTL, long titles and narrow layouts.
- Abort/ignore stale overview/preview requests on workspace/document changes;
  clear protected content on auth/access loss. Opening an action does not silently
  filter chat retrieval or submit a prompt to the current conversation.
- Acceptance: supported one-page/one-slide previews, multi-page/unknown count,
  unsupported format, missing/deleted content, authorization loss, overview failure,
  workspace switching, and accessible menu/dialog behavior.
- Dependency: backend document overview, page/slide count, supported-action and
  browser-safe preview contract; existing NP-20 metadata alone is insufficient.

### Delivery boundaries and validation

- Likely files: frontend/apps/rag-dev-plane/src/App.tsx, api.ts,
  DocumentsPanel.tsx, styles.css, and focused unit tests; create small frontend
  helpers/components as needed. Confirm exact files upon activation.
- Sequence: FP-14, FP-15; FP-16 and FP-17 after their backend contracts arrive.
  Planned commits use each task ID and keep features independently reviewable.
- Implementation validation: permitted frontend type checks, focused unit tests,
  production build and scoped whitespace check. New dependencies, browser
  automation, deployment/auth changes and live-service validation retain existing
  approval gates. No backend implementation or architecture edits during intake.
- FP-13 documentation validation: targeted rereads of phase records and handoff.
  No type checks, tests, builds, browser automation or live services ran.

FP-13 intake completed on 2026-10-03. Phase/backlog and backend handoff records verified by targeted reads; FP-14 through FP-17 remain unimplemented candidates. No application validation commands or live services ran.
