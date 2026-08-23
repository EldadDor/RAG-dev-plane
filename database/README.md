# Database Migrations

PostgreSQL objects are owned by versioned SQL files. The FastAPI process validates the schema but never creates or alters database objects.

Apply the migrations in filename order, then apply the local seed only in a local environment:

```powershell
psql $env:DATABASE_URL -v schema=rag -v table=document_chunks -v vector_dim=768 -f database/migrations/001_baseline.sql
psql $env:DATABASE_URL -v schema=rag -f database/migrations/002_workspace_authorization.sql
psql $env:DATABASE_URL -v schema=rag -v default_workspace_id=local -v local_subject=local-dev -f database/seeds/local_workspace.sql
```

For an existing database, these migrations adopt the current tables and workspace values without dropping data. The local seed is idempotent. Production identity memberships must be provisioned separately by an approved administrative process.

Docker's entrypoint scripts run only when its PostgreSQL data volume is first created. Apply migrations explicitly whenever an existing database is upgraded.
