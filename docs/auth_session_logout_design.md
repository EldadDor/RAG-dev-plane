# NP-24 sign-in, sessions and logout — approved design

**Reviewed:** 2026-10-03. **Status:** G1 and G2 approved; implemented and offline-validated.
The implemented contract is published in `frontend_architecture.md`; deployment
remains unperformed. See `auth_gateway_operations.md` for rollout and limits.

## Chosen approach and boundary

Add a separate FastAPI authentication gateway entry point under `src/app/auth/`,
using Authlib's maintained OIDC client and existing HTTPX/asyncpg infrastructure.
Nginx owns the browser origin, serves/proxies the frontend, routes `/auth/*` to
the gateway, and checks protected API requests through an internal gateway
authorization subrequest. It overwrites all configured identity headers with
the gateway result. The RAG API continues to use `AUTH_MODE=gateway` and checks
workspace membership on every operation. Neither internal authorization nor
the RAG API is publicly reachable. Provide configuration examples; deployment
and running services remain separate operator actions.

The gateway owns authentication, cookies, CSRF, expiry and logout; the RAG API
owns workspace/data authorization. This boundary can also serve another backend
without making its chat API implement Entra authentication.

**Rejected alternative:** Put Entra login and cookie sessions directly into
the RAG API. That couples provider/session concerns to the application and
duplicates the existing gateway boundary across backend runtimes. The chosen
approach costs an additional gateway process and proxy configuration. Authlib
handles OIDC protocol operations; the application still must implement and test
its session/CSRF policy. Resolve and lock a compatible maintained library version
during implementation; the documentation examples are not a version pin.

## Entra and identities

- Authorization code with PKCE S256, one-use state and nonce, tenant-specific
  discovery and exact configured callback origin. Validate signature, issuer,
  audience, expiry, nonce and allowed tenant before creating a session.
- Default workplace policy: one configured organizational tenant, including
  its invited guests. Use `prompt=select_account` for account selection.
  Arbitrary tenants/personal accounts are outside this default and need an
  explicit access policy. Authentication never grants workspace membership.
- Principal key: `entra:<tid>:<oid>` from validated claims; name/email are
  display-only. No automatic mapping from email or from `local-dev` ownership.
  An operator grants memberships to the stable principal; new users can sign
  in and receive an empty workspace list until that grant.
- Username/password, if allowed by tenant policy, is entered on Microsoft's
  page. No application password form, ROPC or local password database.
- Request only `openid profile email`; no Graph or refresh-token requirement.
  Discard provider access/refresh tokens after the login exchange. App logout
  revokes this application's session; global Microsoft sign-out is deferred.

## Local testing and compatibility

`AUTH_PROVIDER=dev` enables two predefined test identities through a local-only,
CSRF-protected selection flow, using the same session store, expiry and logout
logic as Entra. It is rejected outside the local environment. Keep `local-dev`
as one explicit test identity so existing locally owned records remain usable;
the second identity has no access until seeded/granted intentionally. No
arbitrary browser-provided subject/header is accepted. HTTP is restricted to
loopback development origins. A separate Entra development registration tests
the real redirect flow when its credentials/tenant are supplied by the operator.

Existing direct fixed-local API mode remains available for provider-free tests,
and continues to report logout unsupported. Session testing uses the gateway
with API `AUTH_MODE=gateway`; changing real local configuration is not part of
this documentation approval. Local-only process storage resets on restart and
supports one gateway worker; workplace storage is PostgreSQL and fails closed
on outage, with no memory fallback.

## Session persistence and cookie configuration

Migration `009_auth_sessions.sql` uses one gateway-owned table for typed login
transactions, bootstrap contexts and sessions. Store hashes of random 256-bit opaque browser identifiers, stable
principal/display claims, encrypted CSRF token and its verification hash, creation/activity/absolute-expiry
timestamps and revocation state. Login transactions expire after five minutes,
are consumed atomically, and keep state/nonce/PKCE verifier server-side. Encrypt
the entire payload with a gateway-only configured Fernet key; no tokens/verifiers
in cookies or logs. Retain only bounded expired/revoked records and clean them
through an explicit maintenance operation. Separate gateway database credentials
and restrict application access to session tables in deployment instructions.

| Setting | Loopback HTTP development | Workplace HTTPS |
| --- | --- | --- |
| Cookie name | `rag_session_dev` | `__Host-rag_session` |
| Secure | false | true, required |
| HttpOnly / Path / Domain | true / `/` / omitted | true / `/` / omitted |
| SameSite | Lax | Lax |
| Idle / absolute defaults | 30 minutes / 8 hours | 30 minutes / 8 hours |

Expose validated gateway settings for public origin, provider/tenant/client,
store, cookie name/Secure/SameSite, idle/absolute durations and temporary-state
encryption key. Reject unsafe nonlocal combinations; origin comes from configured
values rather than arbitrary Host/forwarded headers. SameSite Lax pairs with a
GET authorization-code callback. Cookie Max-Age reflects the remaining absolute
lifetime; server-side idle/absolute expiry remains authoritative. Rotate the
identifier on login/account switch and revoke the prior session after successful
replacement. Activity is a protected API request, not UI mouse activity; exclude
session-status polling and failed/unauthenticated requests. SSE admission counts
once, stream chunks do not extend the idle timer.

## Approved browser contract

| Route | Owner | Proposed behavior |
| --- | --- | --- |
| `GET /auth/session` | Gateway | 200 with authenticated flag, safe display profile, expiry metadata and CSRF token; anonymous bootstrap has a short-lived CSRF context. No-store; polling does not renew idle expiry. |
| `GET /auth/login` | Gateway | Entra redirect with one-use login transaction; only allowlisted relative return destinations. In dev mode expose the configured identity choices and bootstrap context. |
| `GET /auth/callback` | Gateway | Validate/consume Entra transaction, rotate session, redirect to allowlisted relative destination; safe failure with no provider details. |
| `POST /auth/dev-login` | Gateway | Local-only identity choice from the predefined set; exact-origin and CSRF validation. Create/rotate session; never available in workplace mode. |
| `POST /auth/logout` | Gateway | Exact-origin and CSRF validation; atomically revoke the session, clear cookie using matching attributes, return 204. Already signed-out retry is idempotent with valid bootstrap CSRF. Store failure returns safe 503; do not claim logout success. |

Authorization subrequests are internal-only. Proxy forwards the original method,
origin and CSRF header to the gateway; mutations require exact configured origin
and session-bound CSRF token. OIDC callback uses its transaction protections.
An independently supplied, URL-safe proxy secret also authenticates subrequests;
Nginx captures the original method before creating the GET auth subrequest.
Gateway headers percent-encode UTF-8 values to prevent header injection; decoding
is enabled only by the explicit API session-gateway flag.
Protected APIs return safe 401 rather than an HTML login redirect; errors retain
the existing `{code, message}` convention and private/no-store headers. Do not
cache authorization decisions. Publish concrete JSON shapes/errors/examples
in `frontend_architecture.md` after implementation, before frontend integration.

Update profile logout capability only for configured gateway sessions: supported,
owner gateway, method POST, relative URL `/auth/logout`, application-only scope.
Unconfigured external gateway/fixed-local modes continue to report unsupported.
Frontend aborts active requests on logout, ignores late results, clears protected
state after confirmed success, and handles 401 with the same signed-out recovery.
Logout revokes future admissions in every tab. A request/stream already admitted
can finish; frontend cancellation is required, and this phase does not promise
server-side termination of streams in other tabs or rollback of in-flight writes.

## Migration, rollback and acceptance

Migration 009 is additive and belongs to the gateway, not the RAG vector-store
startup requirements; migration 008 remains a prerequisite for account preferences.
Do not run SQL, grant memberships, provision Entra, change `.env`, start services
or expose ports under G2 implementation approval. Supply an operator rollout
checklist: migrations, credentials, callback registration, private upstream
networking, gateway mode, proxy header stripping and HTTPS/cookie validation.
Rollback restores the previous trusted gateway/configuration and revokes/removes
new gateway sessions; retain additive tables unless separately authorized to drop
them. Never restore a public unauthenticated API. No existing chats, ownership or
preferences are rewritten. Session/token logs must redact secrets.

Offline acceptance: mocked OIDC state/nonce/issuer/audience/tenant failures,
replay and account switching; two-user isolation and membership denial;
cookie flags/deletion; frozen-clock idle/absolute expiry; cross-worker revocation
through mocked SQL; CSRF/origin/redirect/header spoofing; session-store failures;
fixed-local unsupported behavior; account capability/API401/SSE admission rules.
Use provider-free regressions. Real PostgreSQL concurrency/durability, Nginx
header stripping, Entra browser redirects and cookie/logout flows remain explicit
operator-authorized acceptance; mocked tests cannot establish those properties.

## Primary references

- [Authlib Starlette OIDC integration](https://docs.authlib.org/en/v1.5.2/client/starlette.html)
  and [web-client documentation](https://docs.authlib.org/en/v1.7.0/oauth2/client/web/index.html).
- [Nginx authorization subrequests](https://nginx.org/en/docs/http/ngx_http_auth_request_module.html);
  deployed Nginx must include the module.
- [Microsoft authorization-code flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow)
  and [stable identity claims](https://learn.microsoft.com/en-us/entra/identity-platform/id-token-claims-reference).
- [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).
