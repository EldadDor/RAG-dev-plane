# Runtime and Testing — Developer Q&A

1. **Which Python version is the project contract?** Python 3.14.
2. **Why are live integration tests opt-in?** They require the running API, models, and pgvector, unlike deterministic unit tests.
3. **What enables the live test?** `RUN_LIVE_INTEGRATION=1`.
4. **What does the live test verify?** Ingestion, retrieval, grounded sources, workspace isolation, and cleanup.
5. **Why use a project-local pytest base temp directory?** It avoids Windows `%TEMP%` cleanup/permission noise.
