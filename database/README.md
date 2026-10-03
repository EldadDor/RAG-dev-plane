# Database Migrations

PostgreSQL objects are owned by versioned SQL files. The FastAPI process validates the schema but never creates or alters database objects.

Apply the migrations in filename order, then apply the local seed only in a local environment:

```powershell
psql $env:DATABASE_URL -v schema=rag -v table=document_chunks -v vector_dim=768 -f database/migrations/001_baseline.sql
psql $env:DATABASE_URL -v schema=rag -f database/migrations/002_workspace_authorization.sql
psql $env:DATABASE_URL -v schema=rag -v table=document_chunks -f database/migrations/003_chunking_profiles.sql
psql $env:DATABASE_URL -v schema=rag -f database/migrations/004_document_assets.sql
psql $env:DATABASE_URL -v schema=rag -v default_model=nomic-embed-text -v default_dimensions=768 -f database/migrations/005_model_profiles.sql
psql $env:DATABASE_URL -v schema=rag -f database/migrations/006_document_index_metadata.sql
psql $env:DATABASE_URL -v schema=rag -f database/migrations/007_powerpoint_document_type.sql
psql $env:DATABASE_URL -v schema=rag -f database/migrations/008_account_preferences.sql
psql $env:DATABASE_URL -v schema=rag -v default_workspace_id=local -v local_subject=local-dev -f database/seeds/local_workspace.sql
```

For an existing database, these migrations adopt the current tables and workspace values without dropping data. Migration `003_chunking_profiles.sql` marks every existing source and chunk as the `default` profile; it does not re-embed or delete indexed data. Migration `004_document_assets.sql` adds metadata and chunk-link tables for embedded source images; image bytes remain in the configured private asset store. The local seed is idempotent. Production identity memberships must be provisioned separately by an approved administrative process.

Docker's entrypoint scripts run only when its PostgreSQL data volume is first created. Apply migrations explicitly whenever an existing database is upgraded.

## Account preferences — migration 008

Apply `008_account_preferences.sql` before restarting the NP-23 PostgreSQL
writer. Startup requires the table and migration-ledger entry; an older running
process does not gain the account routes until upgraded. This additive migration
stores only trusted subjects, recent-chat display limits and update times.
No backfill, vector re-embedding or chat/document/membership changes are needed.
Docker initialization includes it for new volumes only.

Rollback application code first and retain the table/ledger entry to preserve
preferences. Deleting preference data requires a separately reviewed operation.
Local Qdrant preferences are process-only; gateway/Qdrant preference operations
are explicitly unavailable. Actual SQL rollout and post-restart acceptance are
operator actions and have not been performed by the offline implementation.

## Authentication gateway — migration 009

`009_auth_sessions.sql` is required only for the separate NP-24 PostgreSQL
authentication gateway; the RAG/vector-store startup requirements do not change.
Apply it with the migration role before starting that gateway. The gateway checks
the table and `009_auth_sessions` ledger entry, and never creates tables at startup.
The encrypted records include sessions, short-lived browser CSRF contexts and
one-use OIDC login transactions; the table stores no raw cookies/provider tokens.
Local process storage does not require SQL. This migration is intentionally not
added to the default RAG Docker initialization: gateway rollout is optional and
uses a separate restricted database role.

Rollback retains the additive table and existing application data. SQL execution,
role grants and migration/live durability acceptance have not been performed.
See [gateway rollout/maintenance](../docs/auth_gateway_operations.md).

Migration 007 widens the catalog's canonical type constraint to include
`powerpoint`; it changes no vectors/source records. Apply it before restarting
the PowerPoint-enabled writer. PostgreSQL startup requires the migration ledger
entry. The configured local stack applied it on 2026-10-02.

## Recent document catalog rollout (NP-20)

The configured local stack completed rollout on 2026-10-02: migration 006,
catalog certification, endpoint enablement, and live acceptance. Evidence is in
`../docs/phase_qa/NP20-reconciliation.json` and
`../docs/phase_qa/NP20-live-document-catalog.json`. Other environments still
require the rollout below.

Migration 006 is required by the updated PostgreSQL writer, even while document
listing is disabled. It adds per-model document metadata, revision counters,
model-owned image references, and a deployment-wide readiness gate. It performs
no vector replacement or model calls. Apply it before starting the new backend.

1. Stop older writers and keep `DOCUMENT_LIST_ENABLED=false`. Apply migration
   006 through the normal SQL process. Start only the updated writers.
2. Review the operator report (read-only by default):

   ```powershell
   .venv/Scripts/python.exe scripts/reconcile_document_catalog.py
   ```

3. Resolve reported duplicate chunk identities, conflicting metadata, missing
   assets, unknown workspaces, or unprovisioned ready-profile targets. Missing
   non-ready profile targets are warnings; provisioned archived tables are also
   cataloged to retain their asset ownership. Historical
   source records without chunks cannot establish a model scope; the report
   counts them for operator re-ingestion. Their timestamp is not invented.
   Legacy `document_id` aliases are recovered only when workspace, chunking
   profile, ID and source path exactly match an existing source record. Apply
   adds canonical `doc_id`/type metadata without changing vectors or chunk IDs.
   Chunks with no workspace are excluded and reported as warnings; they remain
   untouched and are unreachable through workspace-filtered retrieval/listing.
   Malformed scoped identities continue to block certification.
4. Apply the reviewed metadata backfill:

   ```powershell
   .venv/Scripts/python.exe scripts/reconcile_document_catalog.py --apply
   ```

   Apply mode first marks the catalog unavailable. All metadata changes and
   certification then commit together; any error rolls back the changes and
   keeps readiness false. The tool holds profile publication locks, so new
   ingestion/warming commits wait. Do not run old writers concurrently: they do
   not honor those locks. No mode calls models or scans document source files.
5. Configure `DOCUMENT_LIST_ENABLED=true`. Gateway/replica deployments need the
   same server-only `DOCUMENT_LIST_CURSOR_SECRET` (at least 32 bytes) in every
   replica. Local single-process mode may use an ephemeral key. Run the
   separately approved live acceptance checks before frontend integration.

The local acceptance runner checks real HTTP pagination/counts and real SQL
authorization/publication fixtures. Its outer transaction always rolls back;
warming uses synthetic vectors and makes no real model calls:

```powershell
.venv/Scripts/python.exe scripts/validate_document_catalog.py --output docs/phase_qa/NP20-live-document-catalog.json
```

New ingestion preserves unknown historical timestamps until a real changed
ingestion establishes them. Reconciliation resets hash/time provenance when it
cannot verify the source version from the actual profile's chunk metadata.
PostgreSQL direct `upsert` is no longer a supported writer: use atomic
`replace_document` publication. Public citation/chunk IDs remain unchanged;
new internal chunk UUIDs include workspace identity to prevent cross-workspace
collisions. Existing UUIDs transition only when a document is replaced.

The local warming CLI now uses the same coordinated service as the API:

```powershell
.venv/Scripts/python.exe scripts/warm_model_profile.py bge-m3 --workspace-id local --source-model-profile default --dry-run
.venv/Scripts/python.exe scripts/warm_model_profile.py bge-m3 --workspace-id local --source-model-profile default --apply
```

The old `--source-profile` chunking flag and unscoped direct-SQL writer are
retired. The new CLI requires a workspace and copies all chunking scopes in it,
without silently modifying unrelated target documents. Warming holds source
and target profile locks while preparing embeddings; a failed job leaves the
target `warming` and can be retried. Locks are intentionally coarse per model
profile for the first implementation, so ingestion commits can wait during a
warm/backfill job.

Qdrant-only deployments return safe 503 for document listing; their process
memory is not advertised as a durable catalog. Rollback disables listing before
deploying old writers; keep additive tables and reconcile before re-enabling.
Migration execution, reconciliation against real data, and live checks have
not been performed as part of the offline implementation task.
