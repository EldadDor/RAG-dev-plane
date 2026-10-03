# NP-23 — Profile and Preferences Design

**Last reviewed:** 2026-10-03
**Status:** NP23-01 G2 Design and G3 delivery approved 2026-10-03; implemented,
offline validated (206 tests passed) and pushed as `5b315c8` to `origin/main`.
NP-23 awaits G4 phase closure.
User instruction: “Approved G2, procced”. Live migration/application rollout
remains separately authorized.

## Scope and current evidence

`src/app/identity.py` supplies a trusted `Principal(subject, display_name, email)`:
fixed server configuration in local mode, trusted gateway headers otherwise.
`GET /workspaces` exposes display name and current memberships through
`WorkspaceStore`. There is no account profile/preferences route or store.
PostgreSQL services share the vector-store pool; versioned SQL and the startup
migration ledger own database changes. Local Qdrant uses process-memory stores.

Expose read-only display name, nullable email and currently authorized workspace
IDs/names/roles. These are identity-provider/configuration assertions, not a
claim of verified email. Keep subject internal. Do not accept identity, workspace
membership, provider configuration or account-administration edits.
The only editable preference is `recent_chat_limit`: 10, 20, 50 or 100,
default 10. It is per principal across workspaces and governs frontend display,
not server session retention or the uncapped session-list response.
Logout ownership/implementation remains NP-24.

## Chosen API

All routes are relative proxy paths and resolve the principal server-side on
every request. They accept no subject/user ID or workspace selector.

| Route | Success | Behavior |
| --- | --- | --- |
| `GET /account/profile` | 200 | Read-only identity, current memberships and supported capabilities. |
| `GET /account/preferences` | 200 | Effective preference, including default 10 when no saved row exists. A read does not insert a row. |
| `PATCH /account/preferences` | 200 | Validate, atomically save and return the effective preference. |

Example profile response for a ready PostgreSQL deployment:

```json
{
  "profile": {"display_name": "Ada Lovelace", "email": null},
  "workspaces": [{"workspace_id": "alpha", "display_name": "Alpha", "role": "member"}],
  "capabilities": {
    "profile_editable": false,
    "preferences": {
      "read": true,
      "update": true,
      "persistence": "server",
      "editable_fields": ["recent_chat_limit"],
      "recent_chat_limit_options": [10, 20, 50, 100],
      "recent_chat_limit_default": 10
    },
    "logout": {"supported": false, "reason": "not_configured"}
  }
}
```

Both preference success responses use this shape:

```json
{"preferences": {"recent_chat_limit": 20}, "persistence": "server"}
```

PATCH body: `{"recent_chat_limit": 20}`. Require a JSON object containing exactly
this field and a strict integer in the allowed set. Reject null, booleans,
strings, floats, out-of-range values, empty bodies/objects and unknown fields
with 422. Do not coerce values or accept attempts to write profile/identity.
Require `application/json`; unsupported media types return a safe 415.
Concurrent writes use last committed write wins; no revision/ETag contract is
needed for this single scalar preference.

All account responses, including errors, use `Cache-Control: private, no-store`
and `Vary: Cookie, Authorization`. Return safe `{code, message}` errors:

| Status | Code | Meaning |
| --- | --- | --- |
| 401 | `authentication_required` | Trusted identity is absent. |
| 415 | `unsupported_media_type` | PATCH content is not supported JSON. |
| 422 | `invalid_request` | Invalid/unknown request fields or values. |
| 503 | `account_preferences_unavailable` | Preference storage is unavailable or unsupported. No silent success. |
| 503 | `account_profile_unavailable` | Profile membership lookup is unavailable. Do not fabricate an empty membership list. |
| 500 | `internal_error` | Unexpected failure; no database/provider details in the response. |

Account-specific unavailable errors need their own handler because the current
global 503 code is `document_list_unavailable`. Preserve existing route errors.
Authenticated users with zero memberships may still read/update their own
preferences; profile returns an empty workspace array. Discover memberships
fresh on each profile request; cached preferences never grant workspace access.

## Storage and availability

Add `AccountPreferenceStore` with PostgreSQL, process-memory and unavailable
implementations in `src/app/services/account_preferences.py`. Use shared
application-lifespan state; never construct a fresh mutable store per request.
Tests explicitly override dependencies and restore application state.

| Deployment | Persistence | Capabilities / lifetime |
| --- | --- | --- |
| PostgreSQL | `server` | Per trusted subject; survives process/browser restart and login, provided the subject is stable. |
| Local identity + Qdrant | `process` | Shared in-memory store with guarded writes; survives requests only until backend restart. No cross-process guarantee. |
| Gateway identity + Qdrant | `unavailable` | Profile is readable through existing membership lookup; preference read/update capabilities are false, editable fields empty, and preference routes return 503. |

For unavailable storage, options/default still describe the supported preference
schema, but the frontend must respect false read/update capabilities.
Logout is explicitly unsupported: reason `fixed_local_identity` in local auth
mode, `not_configured` in gateway mode. Exposing this limitation does not add a
logout operation. NP-24 will supersede it when an actual integration is approved.

Migration `008_account_preferences.sql` adds one table in the configured schema:
`account_preferences(subject TEXT PRIMARY KEY, recent_chat_limit INTEGER NOT NULL
DEFAULT 10 CHECK (recent_chat_limit IN (10,20,50,100)), updated_at TIMESTAMPTZ
NOT NULL DEFAULT now())`, plus its migration-ledger entry. There is no foreign
key to a user table: none exists, and a principal may have zero memberships.
Parameterize subjects and values; an atomic UPSERT changes only that subject's
row. Do not persist display names/emails or copy membership data.

## Alternative and rollout/rollback

Rejected alternative: browser-local preference storage only. It would avoid a
migration, but would not provide a server-authorized preference API or consistent
settings after login/on another browser. The local process fallback is disclosed
as a limited development capability, never represented as durable storage.

Follow the existing startup-ledger pattern: PostgreSQL deployment of the new
writer requires migration 008. Update database instructions and fresh Docker
initialization wiring. Apply the additive migration before restarting upgraded
writers; no existing chat/document rows, vectors or memberships change, and no
backfill is needed. Executing SQL or restarting a service needs separate explicit
operator authorization; G2 implementation approval does not perform rollout.

Rollback application code first; leave the additive table/ledger entry intact
so existing preference values survive a later redeploy. Dropping the table would
lose preferences and needs a separately reviewed operator action. Older writers
do not access it. No new package dependency or configuration secret is proposed.

Gateway writes retain the existing same-origin proxy trust boundary. JSON PATCH
and office gateway origin/CSRF enforcement must be verified in deployment scope;
this phase does not invent an identity provider or relax CORS/proxy settings.

## Implementation and acceptance after G2

Likely files: new account router and preference service/store; existing API
schemas, dependencies, main app, PostgreSQL startup validation; migration 008,
database instructions and Docker migration wiring; focused tests; authoritative
frontend contract and backend-to-frontend readiness entry.

Offline checks cover read-only profile data, nullable email, zero/fresh/revoked
memberships, defaults without writes, strict request validation, update/reload,
independent principals, identity spoof attempts, missing gateway identity,
unavailable storage, safe errors/privacy headers, and process-store lifetime.
Mocked SQL checks parameter binding/subject-scoped UPSERT and ledger requirements;
real SQL durability is reported as unverified until an approved live rollout.
No chat/model/database/browser services are needed for offline tests.

Publish implemented success/error/capability examples in
`docs/frontend_architecture.md` only after validation. FP-16 may then implement
profile/settings; FP-15 may consume the preference without changing session
storage. Neither frontend implementation nor Kotlin runtime parity is implied.
