# NP-24 authentication gateway operations

Implementation is offline-validated; no gateway/proxy/tenant/database rollout
has been performed. The gateway is independent of RAG model/vector startup.
It reads process environment, never `.env` automatically. Configuration examples
are in `.env.example`; do not copy workplace credentials into tracked files.

## Local session testing

Use the loopback Nginx origin `http://localhost:8080`. Configure a single gateway
worker with `APP_ENV=local`, `AUTH_PROVIDER=dev`, `AUTH_SESSION_STORE=memory`,
`AUTH_COOKIE_NAME=rag_session_dev`, `AUTH_COOKIE_SECURE=false`, and a securely
supplied `AUTH_PROXY_SECRET` of at least 32 random bytes shared with Nginx.
Defaults are 30-minute idle and eight-hour absolute expiry; shorten them with
`AUTH_IDLE_SECONDS`/`AUTH_ABSOLUTE_SECONDS` for expiry testing (minimum 60 seconds).
Memory records and the ephemeral encryption key disappear on gateway restart.

After separately approving service configuration/startup, the operator runs
the gateway using this entry point (not the existing RAG entry point):

```powershell
uv run uvicorn app.auth.main:create_gateway --factory --host 127.0.0.1 --port 8001 --workers 1 --no-access-log
```

The RAG API must be private, with `AUTH_MODE=gateway` and
`AUTH_SESSION_GATEWAY_ENABLED=true`. The latter enables decoding the gateway's
percent-encoded UTF-8 identity headers and advertises gateway logout capability.
NP-24 requires the standard `X-Forwarded-User/Name/Email` header names; existing
external gateways retain their prior configuration with this flag false.
Direct fixed-local mode is still useful for provider-free tests and has no logout.

`deploy/auth/nginx.local.conf.template` is an example server block, included in
Nginx's `http` context. Its frontend root and private upstream addresses are
operator-specific. Requires the auth-request module. On systems with envsubst,
render only the shared-secret placeholder, preserving Nginx variables:

```sh
envsubst '${AUTH_PROXY_SECRET}' < deploy/auth/nginx.local.conf.template > /private/nginx/rag.conf
```

Keep the rendered configuration private. Validate it with `nginx -t` before an
explicitly approved reload. Neither validation nor reload was performed here.
Do not use unfiltered envsubst: it would erase the request/auth header variables.
The shared secret is sent only over private upstream connections; private ports
must remain inaccessible to browsers/untrusted networks. Protect internal TLS
connections too when the proxy and services run on separate hosts.

Without frontend login UI, use a same-origin API client: fetch `/auth/session`
to obtain the CSRF token/cookie, fetch `/auth/login` for the predefined choices,
then POST JSON `{"identity":"local-dev"}` to `/auth/dev-login` with the exact
Origin and `X-CSRF-Token`. The response is 303 to `/`. The second identity is
`local-test-2`, with no automatic workspace grant. Cookies alone are insufficient
for mutation requests. Sign-in does not create a chat conversation.

## Workplace Entra rollout checklist

1. Register a confidential web application in the intended tenant. Configure
   the exact HTTPS `/auth/callback` URI and approved user/guest assignments.
   Supply the tenant/client GUIDs and client secret through the workplace secret
   manager; Entra authentication methods/MFA remain controlled by tenant policy.
2. Apply migration 009 using the migration-owning administrative role. Migration
   008 is still required for account preferences. Use a separate gateway DB role
   with schema usage and SELECT/INSERT/UPDATE/DELETE only on `auth_sessions`, and
   read-only migration-ledger access. The RAG runtime role must not own/read
   these session records. No memberships or existing user ownership are migrated.
3. Set nonlocal `APP_ENV`, `AUTH_PROVIDER=entra`, exact HTTPS `AUTH_PUBLIC_ORIGIN`,
   `AUTH_COOKIE_NAME=__Host-rag_session`, `AUTH_COOKIE_SECURE=true`,
   `AUTH_COOKIE_SAMESITE=lax`, `AUTH_SESSION_STORE=postgres`, and a gateway-specific
   `AUTH_DATABASE_URL` with explicit TLS (`sslmode=verify-full` recommended).
   Supply a stable Fernet `AUTH_STATE_ENCRYPTION_KEY` to every gateway replica.
   A Fernet key can be generated offline with `Fernet.generate_key()`; never log
   it or commit it. PostgreSQL mode requires the key even locally.
4. Adapt `deploy/auth/nginx.https.conf.template` with the real hostname,
   certificate/key mounts, frontend root and private service addresses. Apply
   workplace TLS/HSTS and access policy, header stripping and bounded request
   rates. Nginx's `limit_req_zone` belongs in the surrounding `http` context;
   apply a per-client limit to `/auth/` before exposing login/bootstrap publicly.
   Authorization decisions are never cached. Do not expose the RAG API or the
   gateway's internal authorization endpoint. Disable callback query-string logs
   in every reverse proxy, tracing layer and application access logger.
5. Grant specific workspace memberships to verified `entra:<tid>:<oid>` subjects
   through an approved administrative process. Email and display name cannot be
   ownership keys. A newly authenticated user can have an empty workspace list.
6. Perform authorized real SQL concurrency/durability tests, proxy spoof/CSRF
   checks, Entra callback/account-selection tests, expiry and cross-tab logout,
   and frontend stream cancellation/recovery. Verify HTTPS cookie creation and
   deletion in the browser. These checks remain unrun.

The gateway does not request Graph permissions or offline access, retain provider
tokens, manage user passwords or sign users out globally from Microsoft. Restarting
a PostgreSQL gateway preserves sessions when all replicas keep the same key.
Single-tenant organizational/guest access is the initial policy; arbitrary tenant
access requires an explicitly reviewed policy.

## Maintenance, expiry and rollback

Gateway inserts clean expired records and enforce `AUTH_MAX_RECORDS` (default
10,000) across replicas using an advisory transaction lock. Monitor capacity and
503s; expired records can also be removed by an authorized maintenance operation:
`DELETE FROM rag.auth_sessions WHERE expires_at <= now();`. Revoked rows are
retained only until their absolute deadline, supporting safe logout retries.
Never remove active records merely to free capacity without acknowledging that
this signs users out. Auth-request SQL failures return safe 503 through the proxy.

Idle activity means a protected API admission, including automated API polling;
mouse movement and session-status polling do not renew it. Background protected
polling can keep idle sessions alive, while absolute expiry still ends access.
SSE only updates activity at admission. Logout revokes future admissions in every
tab; an already admitted stream/write can finish. Frontend must abort/ignore late
requests, clear protected state on successful logout or 401, and initiate a fresh
sign-in explicitly. Logout can cancel a still-pending stored login transaction;
an authentication callback already admitted may finish, like other in-flight
requests. Global Microsoft sign-out remains separate.

Rotate the encryption key through an approved maintenance window: invalidate
gateway records and update all replicas together; clients must sign in again.
Changing keys without removing records causes safe 503s for unreadable sessions,
not silent authentication fallback. Rotate the proxy secret on both proxy and
gateway together. Logs must not include cookies, CSRF/PKCE values, authorization
codes, tokens, secrets or decrypted session payloads.

Rollback restores the previous trusted gateway/proxy configuration, disables
`AUTH_SESSION_GATEWAY_ENABLED`, and revokes newly introduced sessions. Retain
the additive table/ledger entry unless a separate destructive operation is
approved. Keep upstreams private throughout; no chat/preference/ownership rewrite.
