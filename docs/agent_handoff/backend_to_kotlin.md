# Backend → Kotlin Parity Handoff

This file records delivered backend contract changes that the Kotlin runtime
must mirror or integrate with. Add newest entries below this introduction; do
not rewrite prior entries. The authoritative browser/API contract remains
[`docs/frontend_architecture.md`](../frontend_architecture.md).

## 2026-10-03 — NP-22 recent-chat listing and fallback persistence parity

- **From:** Backend
- **To:** Kotlin runtime owner
- **Type:** API behavior / Requirement
- **Status:** Delivered in Python; Kotlin parity pending
- **Source commit:** `983e8d6` (`NP-22: stabilize recent chat listing`),
  pushed to `origin/main`.
- **Authoritative references:** [session contract](../frontend_architecture.md),
  [NP-22 completed record](../complete_phases.md).

`GET /chat/sessions?workspace_id=<non-empty text>` returns an uncapped bare
array with exactly one entry per owned, active session in the authorized
workspace. It does not gain a server display limit, pagination or cursor: the
client applies its own 10/20/50/100 display choice after deduplicating by
`session_id`. Similar titles are valid distinct sessions.

Both Kotlin persistence implementations must produce the same deterministic
order: `updated_at` descending, null timestamps last, then `session_id` ascending
with case-sensitive ordinal comparison. Filter by stable principal, authorized
workspace and non-archived state before returning records. Treat client refresh
as replacement of its previous list, not append.

`PATCH /chat/sessions/{id}` renames only the current principal's active session
and returns `{"ok":true}`. `DELETE /chat/sessions/{id}` archives only that
session and returns 204; archived sessions disappear from subsequent list/detail
results. The in-memory fallback must persist rename/archive mutations under a
lock and return copied metadata, so callers cannot mutate stored session state.
For ownership/scope failures preserve the safe 404 behavior rather than exposing
another user's session. Do not add a browser-selected subject or workspace
authorization bypass.

**Validation/limits:** Python ran 18 focused offline store/API tests, including
105 sessions, ties/null timestamps, scope and mutation isolation; PostgreSQL
ordering was mocked. No full suite, real SQL/API/browser/model calls, migrations
or service operations validated Kotlin parity. Apparent UI duplicates remain
unconfirmed without a live reproduction.

## 2026-10-03 — NP-23/NP-24 account, identity and session parity

- **From:** Backend
- **To:** Kotlin runtime owner
- **Type:** API change / Requirement
- **Status:** Delivered in Python; Kotlin parity pending
- **Source commits:** `5b315c8` (NP-23), `be26a96` and `8afaefd` (NP-24);
  all pushed to `origin/main`. NP-24 closure: `ec33af8`.
- **Authoritative references:** [account/session contract](../frontend_architecture.md),
  [gateway operations](../auth_gateway_operations.md),
  [approved design](../auth_session_logout_design.md),
  [`009_auth_sessions.sql`](../../database/migrations/009_auth_sessions.sql),
  [`008_account_preferences.sql`](../../database/migrations/008_account_preferences.sql).

### Identity boundary

- Browser sign-in, Entra OIDC authorization-code/PKCE, cookies, CSRF, session
  expiry and logout belong to the shared authentication gateway, not either
  application runtime. The Kotlin service stays private behind the same
  Nginx/gateway boundary and never accepts a browser-selected user ID, identity
  header or bearer cookie directly.
- The gateway forwards trusted `X-Forwarded-User`, `X-Forwarded-Name` and
  `X-Forwarded-Email` only after session admission. In session-gateway mode each
  value is percent-encoded UTF-8; Kotlin must decode strictly once and reject
  malformed values. The stable Entra subject is `entra:<tenant-guid>:<object-guid>`.
  Display name/email are display-only, never ownership keys.
- Fixed local API mode remains `local-dev` and has no logout. Local browser
  session testing uses the gateway's two fixed choices: `local-dev` and
  `local-test-2`; the latter receives no automatic workspace grant.
- Kotlin must revalidate workspace/data membership from the stable subject on
  every protected operation. Authentication does not itself grant access.

### Required session behavior

| Area | Kotlin parity |
| --- | --- |
| API admission | Accept requests only after gateway authentication. Missing, expired or revoked identity returns safe JSON 401, never an HTML redirect. |
| Mutations | Gateway validates exact Origin plus `X-CSRF-Token` on protected POST/PATCH/PUT/DELETE, including chat and streams. Kotlin must not expose a direct bypass. |
| Logout | `POST /auth/logout` is gateway-owned; Kotlin neither clears cookies nor claims logout success. Future admissions are revoked across tabs. |
| 401 recovery | Clear protected state, abort/ignore late work and explicitly sign in again. Do not replay mutations or streaming POSTs. |
| SSE | Gateway admits once and stream chunks do not extend idle expiry. Preserve proxy buffering-off behavior; already admitted work can finish. |

Gateway cookies are opaque, HttpOnly, host-only and path `/`. Defaults are
30-minute idle and eight-hour absolute expiry; server records are authoritative.
Workplace uses HTTPS with `Secure`, `SameSite=Lax` and `__Host-rag_session`;
loopback local HTTP uses `rag_session_dev`. Kotlin should not create or parse
these cookies.

### Account/profile and preferences parity (NP-23)

- `GET /account/profile` is server-derived and read-only, with no query
  selectors. It returns display name, nullable email, current memberships and
  capabilities. Responses/errors use `Cache-Control: private, no-store` and
  `Vary: Cookie, Authorization`.
- On a deployed session gateway, profile logout capability is:

  ```json
  { "supported": true, "owner": "gateway", "method": "POST", "url": "/auth/logout", "scope": "application" }
  ```

  Fixed-local mode returns `{"supported":false,"reason":"fixed_local_identity"}`;
  an external gateway without this integration returns
  `{"supported":false,"reason":"not_configured"}`.
- `GET /account/preferences` and `PATCH /account/preferences` support only
  `recent_chat_limit`: integer `10`, `20`, `50` or `100`, default `10`. PATCH
  requires JSON, has no query selectors and rejects coercion/extra fields.
  PostgreSQL persistence is per stable subject in migration 008; reads do not
  write the default. Storage is durable on PostgreSQL, process-lifetime under
  local Qdrant, and explicitly unavailable for gateway + Qdrant.

### Shared rollout requirements and non-goals

- Migration 009 is gateway-owned and must be applied with a restricted gateway
  role before PostgreSQL session mode starts. Kotlin must not read/write
  `rag.auth_sessions`. Migration 008 is required where Kotlin exposes account
  preferences against PostgreSQL.
- Use the Nginx operations guide as the security boundary: internal auth
  subrequests require the proxy secret, client identity headers are stripped,
  decisions are not cached and callback query strings are not logged.
- Entra registration, secrets, database grants, migrations, proxy configuration,
  browser acceptance and real SQL durability/concurrency tests remain unrun and
  require a separately activated, operator-approved rollout task.
- The gateway provides application logout only. It does not globally sign users
  out of Microsoft, transfer `local-dev` data to Entra users, or terminate work
  already admitted before logout.

### Kotlin owner action

1. Compare trusted-principal extraction, authorization, account responses and
   error/privacy headers to the published contract.
2. Route Kotlin through the same gateway in local two-identity and workplace
   Entra modes; remove/disable any direct browser-authentication path.
3. Coordinate a separately approved rollout for migration 008 where applicable,
   migration 009 gateway setup, proxy/Entra configuration and real browser/SSE/
   logout validation.

**Validation status:** Python's provider-free suite passed 266 tests, covering
synthetic RSA/JWKS claims validation, PKCE, callback replay, cookie/expiry/CSRF,
revocation and account membership/capability behavior. It does not validate
Kotlin, real PostgreSQL, Nginx, Entra or browser behavior.
