# Current Backend Work Phase

**Last reviewed:** 2026-10-06
**Status:** DOC-03 RAG ingestion and chat flow diagram — In progress.

**Scope:** Documentation only. Create a Mermaid flow showing the complete document ingestion and chat/retrieval/synthesis paths, key stores, model/provider boundaries and relevant authorization/workspace boundaries. Add it to the authoritative architecture documentation.

**G1 approval:** User instructed “start DOC-03” on 2026-10-06; this approves intake only.
**Affected area:** Shared backend architecture documentation.
**Rough validation plan:** Trace both paths through current implementation and architecture docs; check Mermaid syntax/rendering and links; run `git diff --check`. No application tests or services are expected for this documentation task.

| ID | Task | Status | Request / evidence |
| --- | --- | --- | --- |
| DOC-03-01 | Trace and diagram document ingestion and chat flows in Mermaid | In progress | Intake approved 2026-10-06. Include extraction/chunking/embedding/index persistence and chat authorization/retrieval/context/synthesis/streaming, with key stores and provider boundaries. |
