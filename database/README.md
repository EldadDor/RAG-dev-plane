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
psql $env:DATABASE_URL -v schema=rag -v default_workspace_id=local -v local_subject=local-dev -f database/seeds/local_workspace.sql
```

For an existing database, these migrations adopt the current tables and workspace values without dropping data. Migration `003_chunking_profiles.sql` marks every existing source and chunk as the `default` profile; it does not re-embed or delete indexed data. Migration `004_document_assets.sql` adds metadata and chunk-link tables for embedded source images; image bytes remain in the configured private asset store. The local seed is idempotent. Production identity memberships must be provisioned separately by an approved administrative process.

Docker's entrypoint scripts run only when its PostgreSQL data volume is first created. Apply migrations explicitly whenever an existing database is upgraded.

## Recent document catalog rollout (NP-20)

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
