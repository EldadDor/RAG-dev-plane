# Recent Document Metadata API — NP-19 Design

**Status:** Design complete; proposed contract, not implemented
**Prepared:** 2026-10-02
**Owner:** Backend team
**Request:** Frontend FP-10, FP-11, FP-12, recorded in
[`agent_handoff/frontend_to_backend.md`](agent_handoff/frontend_to_backend.md).
**Authorization:** User approved detailed API design. Runtime implementation,
migration application, backfill execution, and live validation are subsequent work.

## 1. Outcome and boundaries

Provide a read-only, workspace-authorized list of documents available in the
same model/chunking scope used by chat. Each item supplies a stable document ID,
safe title and filename, canonical document type, successful ingestion time when
known, and exact indexed chunk count. The frontend applies configurable size
thresholds and type colors to these values.

The initial API has one list route. It does not introduce upload, ingestion,
deletion, administration, document download, document selection for retrieval,
search/filter controls, or a profile-selector UI. Existing chat, citations,
sessions, and assets keep their public contracts. No list request invokes an
embedding/chat provider, reparses a source file, or scans the source filesystem.

All decisions below are the proposed implementation target. The authoritative
implemented contract remains `frontend_architecture.md`; publish final wire
examples there only after the endpoint and acceptance checks are implemented.

## 2. Current implementation evidence

| Current behavior | Consequence for the design |
| --- | --- |
| `src/app/chunkers/ids.py` hashes the supplied source-path string into `doc_id`. | Reuse the opaque ID and preserve citation correlation; do not promise identity across renames or differently spelled paths. |
| Migration 003 keys `rag.source_documents` by workspace, chunking profile, and document; it has no model-profile axis. | Its latest hash and `updated_at` can describe a different model profile from the one being listed. |
| `PgVectorStore.replace_document` replaces one model table's chunks and shared source/assets in a transaction. | Add per-model document metadata to that same transaction; shared source timestamps cannot be the new API's truth. |
| Ingestion does not persist `Document.title` at document level; titles occur in chunk payloads. | Persist a safe title/name directly, including zero-chunk documents. |
| Ingestion's unchanged result reports `chunks_indexed=0`. | That is work performed in this request, not the retained index size; never display it as the document's count. |
| `ModelProfileWarmer` uses batch `upsert` without per-document replacement or ingestion-time provenance. | Warming must gain document completion bookkeeping and remove stale target chunks before exact counts can be certified. |
| `QdrantVectorStore` keeps document metadata in process memory, while points survive restarts; replacement is delete then upsert. | It cannot meet a durable, atomic catalog contract by simply exposing its `_documents` dictionary. |
| `load_directory` distinguishes loaded files from failed loads, but `ingest_path` discards the failure list before stale-document cleanup. | Preserve last successful records for failed files; failure must not look like confirmed deletion. |
| Stored source types are `markdown`, `html`, `pdf`, `word`, `text`, `code`, `unknown`. | Use those values as the canonical browser type taxonomy. |

## 3. Route and query contract

```http
GET /workspaces/{workspace_id}/documents?limit=25
Accept: application/json
```

Use the existing relative Vite/Nginx proxy route. The browser URL-encodes the
workspace ID as a single path segment and sends no identity header or user ID.

| Parameter | Rules |
| --- | --- |
| `workspace_id` | Required, non-empty text path segment, with the same workspace identity semantics as existing routes. No implicit workspace fallback. |
| `limit` | Integer, default 25, range 1–100; reject values outside the range rather than clamp. |
| `cursor` | Optional opaque token, maximum 4096 characters. Absent means begin a new traversal. Empty/malformed tokens are invalid. |
| `model_profile` | Optional configured profile name; same letters/numbers/underscore/hyphen validation as chat. Resolve omission with the same `MODEL_PROFILE` resolver as chat. |
| `chunking_profile` | Optional configured profile name; resolve omission with the same `DEFAULT_CHUNKING_PROFILE` resolver as chat. |

The frontend initially omits both profiles. API profile parameters support
explicit contract validation and future callers; they do not authorize a UI
selector. Return resolved names in every response. Never merge model tables or
chunking profiles into a count.

For continuation requests, repeat the same effective scope and `limit`; a cursor
does not override query parameters. If omitted profile defaults changed since
the first page, restart through the list-changed error below.

There is no arbitrary "last N days" filter or hidden document cap: "recent"
means all currently published documents ordered by latest successful ingestion.
Load-more pagination makes every item reachable while the scope is unchanged.
No total-document-count field is needed for initial delivery.

## 4. Success response

```json
{
  "workspace_id": "local",
  "scope": {
    "model_profile": "bge-m3",
    "chunking_profile": "default"
  },
  "items": [
    {
      "doc_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "title": "טיפול בשגיאות כלליות",
      "file_name": "general_errors_handling.docx",
      "document_type": "word",
      "last_ingested_at": "2026-10-02T08:30:15.123456Z",
      "indexed_chunk_count": 42
    }
  ],
  "page": {
    "limit": 25,
    "has_more": false,
    "next_cursor": null,
    "list_revision": "18",
    "generated_at": "2026-10-02T08:31:00.000000Z"
  }
}
```

Example IDs, times, counts, and revisions are illustrative. An empty authorized
scope returns `200` with `items: []`, `has_more: false`, and `next_cursor: null`.

| Field | Type and meaning |
| --- | --- |
| `workspace_id` | Non-empty text; the authorized requested workspace. |
| `scope` | Exactly the resolved model and chunking names. |
| `items` | At most `limit` items, unique by `doc_id` within this scope. |
| `doc_id` | Existing opaque document ID, matching source citations; not a file path, URL, or authorization token. |
| `title` | Non-empty display string, at most 300 Unicode code points. |
| `file_name` | Non-empty basename only, at most 255 Unicode code points. |
| `document_type` | Canonical string from the type table below. Clients must tolerate future unknown values. |
| `last_ingested_at` | RFC 3339 UTC timestamp, or `null` when historical successful-ingestion time cannot be established. |
| `indexed_chunk_count` | Non-negative integer; exact count in the published document version of this scope. No `null`, estimate, cross-profile sum, or assets counted as chunks. |
| `page.limit` | Effective page size, identical to requested/default size. |
| `page.has_more` | True iff another item exists in this traversal. |
| `page.next_cursor` | Opaque string iff `has_more` is true; otherwise `null`. |
| `page.list_revision` | Opaque decimal string identifying the scope's current published list version; a string avoids JavaScript integer precision issues. |
| `page.generated_at` | Server response timestamp, not an ingestion time or a historical snapshot promise. |

### Display metadata and types

Choose title from the loader's `Document.title`, then sanitized filename, then
`Untitled document`. Extract basename server-side with support for both slash
styles. Strip control characters and bidi override/isolate formatting controls,
normalize whitespace, and truncate to the defined limits; retain Hebrew and
other ordinary Unicode text. Render as text in the browser with appropriate
direction isolation. A title containing an absolute path is rejected as display
metadata and falls back to filename. This sanitization is a display boundary,
not a guarantee that a user-authored title contains no sensitive words.

Only allowlisted fields appear in the response. Exclude `source_path`, root or
repository paths, source content/snippets, hashes, chunk text, raw metadata,
storage targets, provider identifiers, credentials, and asset storage keys.
Identical basenames in different directories remain separate documents; do not
expose internal directories to disambiguate them in this release.

| Canonical type | Display suggestion | Loader mapping |
| --- | --- | --- |
| `word` | Word | `.docx` |
| `pdf` | PDF | `.pdf` |
| `markdown` | Markdown | `.md`, `.mdx` |
| `html` | HTML | `.html`, `.htm` |
| `text` | Text | `.txt` |
| `code` | Code | All current CodeLoader source/configuration extensions, including JSON, YAML, TOML, SQL, and Kotlin scripts. |
| `unknown` | Unknown / Other | Missing or unsupported stored source type. |

The backend uses the loader's persisted source type, not browser extension
guessing. Category thresholds and badge colors remain frontend configuration.
The backend returns no `size_category` or color fields.

## 5. Identity, time, count, and lifecycle decisions

Document identity is `(workspace_id, doc_id)`; publication identity adds
`model_profile` and `chunking_profile`. Same identity re-ingested with changed
content remains one list item. A renamed/moved file, or the same path supplied
with different spelling, may have a different current hash ID. Path normalization
and cross-rename identity migration are outside this API.

`last_ingested_at` records the successful persistence of a newly ingested or
changed source version into this scope. Set it from the database clock at the
publication write after obtaining the writer lock, and expose it only on commit.
It is not file modification time, provider-call time, global source `updated_at`,
or model-warming time. An unchanged skip preserves its original time and count.
A changed successful ingestion updates both and moves the document forward.

Count exactly the persisted chunk rows for this document in the selected model
target and selected chunking profile after replacement. Normal replacements
derive the count from committed rows; per-document uniqueness must ensure one
row per actual chunk. Duplicate ingestion, model warming, multiple model tables,
assets, or repeated directory scans must not inflate it. Reconciliation may
repair a count and invalidate pagination without altering ingestion time.

| Event | Published list behavior |
| --- | --- |
| First ingestion is loading/embedding | No new item until document replacement and metadata commit. |
| First ingestion fails | No new item. No failed/pending row in this discovery API. |
| Re-ingestion is in progress | Keep the previous successful version, count, and timestamp. |
| Re-ingestion fails | Retain the previous successful version. |
| Re-ingestion commits changed content | Atomically replace count, safe metadata, and timestamp; increment scope revision. |
| Unchanged skip | Preserve published metadata, count, timestamp, and revision. |
| Empty/whitespace source or no valid chunks | Commit replacement with zero chunks and publish count 0; remove any previous chunks. An image-only document can appear with count 0. |
| Dry run | No publication, timestamp, count, or revision change. |
| Model warming | Publish each completed target document with the source scope's known ingestion time, or null if unknown; model copying must not label old information as newly ingested. |
| Warming fails partway | Do not publish an incomplete target document; the target profile remains unavailable until ready. Complete target documents may be retained for safe retry. |
| Confirmed missing source after a successful directory scan | Delete its publication and chunks in the affected scope transaction; increment revision. |
| Source fails to load during a directory scan | Preserve its previous publication and chunks. A skipped supported file is not confirmation of deletion. |
| One model/chunking scope deletes a document | Remove only that scope's publication; other scopes remain independent. |
| Manual unsupported database/vector mutation | Requires operator reconciliation before the list can be certified; do not claim it as a supported write path. |

Directory ingestion may commit several documents independently. If a later
document fails, earlier successful commits remain visible. "Successful ingestion"
is per document, not a promise that an entire directory job was atomic.

## 6. Ordering and pagination consistency

Order by `last_ingested_at DESC NULLS LAST`, then `doc_id ASC` using a fixed
bytewise/C collation. Historical items with unknown time are included after
known-time items, ordered by ID. The UI displays "Ingestion time unavailable"
and does not label them newly ingested.

Use keyset pagination, not offset pagination. Fetch `limit + 1` rows to determine
`has_more`; return only `limit` rows. Encode a null-time discriminator, last
timestamp when present, and last document ID in the continuation position.
The keyset predicate follows the same null ordering and collation.

Choose revision-checked traversal instead of claiming a frozen snapshot across
HTTP requests. Every observable list change increments a monotonically
increasing revision for `(workspace, model profile, chunking profile)`. Read the
revision and page rows in one short PostgreSQL repeatable-read transaction.
A writer serializes on the scope revision row and commits its vector mutation,
publication mutation, and revision increment in the same transaction.

Continuation succeeds only if its revision still matches. Any intervening
insertion, removal, metadata/count correction, or changed ingestion returns
`409 document_list_changed`. The frontend replaces its accumulated list with a
new first-page traversal rather than appending an inconsistent page. This gives
deterministic, duplicate-free traversal during stable periods. Frequent ingestion
can cause restarts; immutable historical snapshot storage is a future extension
if that becomes a product requirement.

### Cursor format and validation

Clients treat the cursor as opaque. Server format: versioned base64url JSON plus
HMAC-SHA256 signature. Payload carries workspace, resolved profiles, effective
limit, list revision, last-position fields, issued/expiry times, and a keyed
fingerprint of the authenticated subject (never the raw subject). Tokens expire
15 minutes after issuance; subsequent pages retain the first token's expiry.
The signing key is server-only and shared across replicas; add typed
`DOCUMENT_LIST_CURSOR_SECRET` configuration with no browser exposure. A local
single-process deployment may generate an ephemeral key; restarting invalidates
its tokens. Gateway deployments require a configured secret through normal
secret injection, and startup must fail if it is absent when this route is enabled.

Check length and decoding before parsing bounded payloads; verify signature in
constant time, version, expiry, scope, subject fingerprint, limit, and position
types. Malformed/tampered/cross-subject/cross-workspace or explicitly changed
query scope is `422 invalid_request`. Expired valid tokens and changed configured
defaults are `409 document_list_changed`, permitting a first-page restart.
Key rotation invalidates old signatures as `422`; frontend offers a fresh reload.
Cursors never grant workspace access and must not be logged in full.

## 7. Authorization, headers, errors, and recovery

Use `get_principal` and `require_workspace_access` for every page. The gateway
derives office identity; local mode uses the existing fixed subject. Both owner
and member can list the shared workspace corpus. Listing is workspace-wide,
not restricted to the uploader. The current product has workspace membership
authorization, not document-level ACLs. Any future document ACL must apply before
pagination and count visibility.

Authenticate, validate basic path/query syntax, authorize the workspace, then
resolve profiles and validate the cursor. Unknown and unauthorized workspaces
return the same safe 403 behavior as current workspace-scoped routes. Revalidate
membership even for a signed continuation token. Queries always predicate on
workspace and both profile axes. Use registered/validated storage identifiers
for SQL; never concatenate client profile strings into table names.

Success and error responses use `Content-Type: application/json`,
`Cache-Control: private, no-store`, and `Vary: Cookie, Authorization` so a shared
proxy never reuses metadata between authenticated callers. No ETag/304 in v1.
The gateway must also prevent caching by its trusted identity-header mechanism;
`Vary` alone cannot cover a server-injected identity header. Existing proxy
identity stripping/injection requirements continue to apply.

| HTTP | Code | Trigger | Frontend recovery |
| --- | --- | --- | --- |
| 401 | `authentication_required` | Gateway identity absent. | Existing sign-in/reload path; clear protected list. |
| 403 | `workspace_access_denied` | Unknown workspace or missing/revoked membership. | Clear list, refresh workspace discovery, recover selection. |
| 422 | `invalid_request` | Invalid limits, query/profile values, cursor signature/scope/subject/shape; explicit unknown or non-ready profile. | Correct state or offer fresh reload; never show raw server detail. |
| 409 | `document_list_changed` | Revision changed, valid token expired, or omitted-profile default changed. | Restart page one; show a short list-updated notice. |
| 503 | `document_list_unavailable` | Catalog disabled/unsupported, not initialized, configured default unavailable, reconciliation not complete, or catalog dependency temporarily unavailable. | Retry control; preserve chat usability. |
| 500 | `internal_error` | Unexpected backend error. | Safe retry UI. |

The two new error codes require explicit endpoint error mapping in
`src/app/main.py` or a typed endpoint exception; throwing a generic 409/503
`HTTPException` is insufficient until the safe-envelope mapper supports them.
Do not reuse an upstream model failure code: listing does not call a model.

```json
{ "code": "document_list_changed", "message": "The document list changed. Reload it to continue." }
```

```json
{ "code": "document_list_unavailable", "message": "The document list is temporarily unavailable." }
```

Do not disclose registry statuses, missing table names, SQL text, paths, cursor
contents, or upstream exception strings. Log diagnostics server-side under a
request ID. Authorized empty data is 200, not 404. There is no document-detail
route in this release.

## 8. Persistence and service design

### PostgreSQL first delivery

Add versioned migration `006_document_index_metadata.sql`; application code only
validates migrated objects and never performs DDL. Keep existing source rows and
vector tables intact. Add these proposed objects:

| Object | Columns / constraints |
| --- | --- |
| `rag.document_index_metadata` | `workspace_id TEXT`, `model_profile TEXT`, `chunking_profile TEXT`, `doc_id TEXT`; composite PK on all four. `title TEXT NOT NULL`, `file_name TEXT NOT NULL`, `document_type TEXT NOT NULL`, `content_hash TEXT NULL` (internal per-model skip/version provenance), `last_ingested_at TIMESTAMPTZ NULL`, `indexed_chunk_count BIGINT NOT NULL CHECK >= 0`, `updated_at TIMESTAMPTZ NOT NULL`. Enforce display lengths, canonical type, and count maximum equal to JavaScript's safe integer 9007199254740991. |
| `rag.document_list_revisions` | Composite PK on workspace/model/chunking scope; `revision BIGINT NOT NULL CHECK >= 0`, `updated_at TIMESTAMPTZ NOT NULL`. Missing authorized initialized scopes read as revision 0 and empty data. |
| Listing index | `(workspace_id, model_profile, chunking_profile, last_ingested_at DESC NULLS LAST, doc_id COLLATE "C" ASC)` on metadata. |

Workspace and model-profile keys reference existing workspaces/registry where
applicable. Do not cascade these rows from `source_documents`: that table lacks
the model-profile axis and currently deletes records shared by multiple models.
No registry of chunking profiles is stored in SQL; configuration resolves that
axis. Use explicit per-scope deletion in the same transaction as vector removal.

Introduce `DocumentCatalogStore` and `DocumentCatalogService`:

- The store reads authorized scoped pages and revision using a consistent
  transaction. PostgreSQL mutation methods share the vector-store connection;
  they must not independently commit catalog changes after vector writes.
- The service resolves scope exactly as chat does, validates/builds cursors,
  sanitizes response fields, and returns typed schema objects.
- The router depends on principal/membership/catalog service and has no
  dependency on embedding or chat clients. Mount alongside active routers.
- Add response models in `api/schemas.py`, the new documents router, dependency
  construction, catalog/cursor settings, and explicit safe error mapping.

### Required write-path alignment

For normal ingestion, prepare embeddings before publication. In one transaction:
ensure/lock scope revision row, serialize a document's replacement, replace its
chunks, persist existing source/asset changes, compute count, upsert the safe
metadata projection with the document's loader title, set ingestion time, and
increment revision once. Concurrent writes serialize and last successful
publication wins; times are assigned after lock acquisition so commit order
does not reverse list ordering. Readers see the entire old or new projection.

Replace the unchanged-skip hash check with per-model projection provenance;
the current shared `source_documents.content_hash` cannot prove that one model
table holds the requested version. A backfilled unknown hash cannot certify an
unchanged skip: safely replace that scope once to establish provenance. Ensure
zero-chunk documents participate in the same skip bookkeeping. Fix the existing
"no valid chunks" branch to publish an empty replacement instead of leaving old
chunks in place.

For warming, group by document and chunking scope. Preserve source publication
metadata/time/hash when trustworthy, prepare a complete document's vectors, then
replace target chunks and its projection transactionally. Remove old target
chunks for that document, including old surplus chunks; retry must not leave a
partially copied document counted as complete. A profile becomes ready only
after every document in that warm job is complete. Serialize warm and ingestion
operations affecting the same target profile/scope; capture and recheck source
revision, and abort/restart a warm traversal if the source changed. Source
deletions must not be silently undone by stale warm data. Existing unrelated
target documents are retained unless an explicit future full-sync mode defines
deletion policy.

For directory cleanup, retain supported-file load failures as protected
identities and perform confirmed deletion only within the actual scan's
recursive/non-recursive coverage. A partial/non-recursive scan must not delete
previously ingested descendants. Revalidate the affected records while holding
the scope writer lock. Delete target chunks and projection together. Shared
source/assets cleanup must occur only when no model projection still needs
them; the existing unconditional shared-row cleanup cannot define cross-model
document lifetime.

A list revision changes only when the public projection changes. Internal audit
time writes and unchanged skips do not invalidate it. Direct supported writes
outside ingestion/warming must route through the same publication coordinator.

### Qdrant and fallback boundary

First production delivery is PostgreSQL-backed. A fake in-memory catalog is
permitted for isolated tests, not advertised as durable Qdrant behavior. A
Qdrant deployment without a durable catalog returns safe 503 on this new route;
its existing chat/ingestion paths remain available. Do not return a misleading
empty 200 based on a newly restarted in-memory dictionary.

Qdrant parity requires separately scoped durable metadata plus recoverable
staged publication across vector and catalog stores; deletion/upsert is not a
cross-store transaction. Define restart recovery, durable per-scope revisions,
and zero-chunk persistence before enabling the same contract there.

## 9. Migration, historical backfill, rollout, and rollback

1. Implement offline store/router/lifecycle checks behind server-side
   `DOCUMENT_LIST_ENABLED=false` by default. Disabled route returns safe 503.
   Configure cursor signing; do not enable client UI on a proposal alone.
2. Review/apply migration 006 through the normal SQL process. Do not rebuild
   existing vectors, rerun embeddings, or rewrite existing document IDs.
3. Run an operator-controlled metadata backfill with dry-run/report mode first,
   during a write pause or with publication locks. Enumerate registry-validated
   provisioned model targets, group actual rows by workspace/chunking/doc ID,
   calculate exact counts, and sanitize recovered title/name/type. Never union
   profiles into counts; flag conflicting metadata or duplicate identities.
4. Historical chunk `created_at` may be warming/upsert time, and shared source
   `updated_at` may belong to another model. Set `last_ingested_at=null` unless
   reliable per-scope evidence exists. Keep content hash null unless provenance
   is established. Do not fabricate successful ingestion time or assign the
   backfill run's time as recency.
5. Include orphan chunk groups with safe metadata recovered from their own
   payloads, and report the orphan condition. Exclude deleted/no-longer-present
   groups. Historical zero-chunk source rows cannot be assigned to a model
   reliably: report them for operator re-ingestion, rather than invent profile
   membership. New zero-chunk ingestions are fully supported.
6. Reconcile each publication count against its model table, verify no path or
   content leakage, initialize revisions, and record unresolved data issues.
   Block enablement for scopes whose counts cannot be certified. This requires
   persisted server-side readiness tracking or a deployment-wide readiness gate;
   a worker-local flag is insufficient across replicas. Initial delivery uses
   deployment-wide enablement after all exposed ready-profile scopes reconcile.
7. With separately authorized live validation, exercise membership, scope/count
   parity, re-ingestion, directory cleanup, warming, and pagination. Publish
   implemented examples/errors in `frontend_architecture.md`, respond through
   `backend_to_frontend.md`, then frontend may activate FP-10 followed by FP-11/12.

Rollback disables the new route/UI and leaves existing chat contracts and vector
data intact. Keep additive metadata tables for diagnosis. Rolling back to a
writer version that does not maintain the projection requires disabling listing
before deployment; reconcile before re-enabling. Removing additive tables is a
separately reviewed migration, not an automatic rollback operation.

## 10. Frontend acceptance and refresh behavior

- Request page one when workspace selection becomes valid; clear prior workspace
  items immediately and abort/ignore old responses using a scope/request marker.
- Offer a Refresh action and refresh on returning to the documents panel. No
  polling or SSE channel is required in the initial release. Reset pagination
  on refresh. Show loading, empty, error/retry, and load-more states.
- Append only pages for the same workspace, effective profile scope, and list
  revision. A 409 starts a new first page; permit one automatic restart for that
  user action, then offer Refresh if mutations continue, avoiding retry loops.
- Clear protected metadata on 401/403. Initial 503/500 shows unavailable/retry;
  if a refresh/load-more fails, keep existing authorized items visibly stale.
- Display the exact count, including 0. Suggested frontend defaults are Small
  0–49, Medium 50–199, Big 200–999, Extra-Large 1000+; these are configurable
  product defaults, not server classifications. Missing/invalid counts in a
  malformed response must show Unknown rather than 0/Small.
- Use separate text badges for size and canonical type, configured colors with
  readable contrast, and a neutral Unknown/Other type fallback. Handle Hebrew,
  long text, narrow layouts, keyboard access, and screen-reader labels.
- A null timestamp shows unavailable history. A document row has no retrieval
  filtering effect. Do not invent a document download/detail link from its ID.

## 11. Planned implementation tasks and acceptance checks

Proposed next phase NP-20, with independently reviewable commit boundaries:

| ID | Work / intended commit boundary |
| --- | --- |
| NP20-01 | `NP-20: add document metadata schema and catalog store` — migration, readiness checks, listing index, store, count/revision constraints. |
| NP20-02 | `NP-20: coordinate document publication across profiles` — ingestion skip/provenance, empty replacement, warming completion, failed-file protection, scan coverage, shared lifecycle. |
| NP20-03 | `NP-20: expose authorized recent document listing` — route, schemas, profile resolver reuse, cursor validation, safe errors, configuration. |
| NP20-04 | `NP-20: backfill and validate document metadata` — dry-run metadata tool, reconciliation, offline regression coverage and separately approved live checks. |
| NP20-05 | `NP-20: publish validated frontend document contract` — authoritative examples, response handoff, implementation evidence and phase closure. |

Required offline implementation coverage:

1. Owner/member success; absent identity; unknown/revoked workspace; no
   cross-workspace records or counts; continuation rechecks membership.
2. Omitted profiles match chat configuration; explicit scope isolation; invalid
   and non-ready profiles; changed defaults; safe unsupported-storage failure.
3. Exact counts after changed/unchanged ingestion, zero chunks, surplus removal,
   failed re-ingestion, concurrent writes, and model warming; other scopes remain
   independently correct. Historical hash/timestamp provenance is never guessed.
4. Stable tie ordering, unknown-time ordering, bounded pages, full traversal,
   `limit+1` behavior, empty page semantics, changed revision restart, no duplicate
   rows in a stable traversal, malformed/expired/tampered/cross-user cursors,
   null-time keysets, replica key consistency, and cursor secret absence.
5. Directory load failure preserves old success; non-recursive scans preserve
   descendants; confirmed scoped deletion preserves other model publication
   and assets; warmer cannot resurrect concurrently deleted source data.
6. Responses contain only allowlisted fields; unsafe titles, both path styles,
   fallback filenames, canonical/unknown types, Hebrew and long Unicode metadata.
7. GET never calls providers, source loaders, or filesystem scanning; GET does
   not perform catalog mutations; safe JSON envelopes and no-store headers.
8. Backfill dry-run writes nothing and calls no providers; historical unknowns,
   orphan groups, duplicate/conflicting metadata, and interrupted restart are
   reported consistently. Existing chat/session/asset regressions still pass.

Live checks after separate authorization use two principals/workspaces and two
model profiles, actual SQL row-count comparisons, failed and successful
replacement, zero-chunk records, directory cleanup and warming, and a changed
list between browser pages. Record evidence before contract publication.

## 12. Completion of this design task

This design resolves the handoff's requested fields, ordering/tie-breaker,
pagination, refresh behavior, lifecycle visibility, profile semantics, safe
metadata exposure, persistence requirements, and validation plan. It identifies
current write-path gaps rather than presenting the proposed route as live.
Implementation approval can use this document as the NP-20 scope; it also covers
the necessary lifecycle corrections for trustworthy metadata. No application
code, database schema, frontend code, or service configuration changed during
NP-19 design.
