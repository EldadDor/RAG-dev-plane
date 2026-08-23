# Testing

This project has two intentionally separate test layers:

1. unit and API-contract tests run without the application, PostgreSQL,
   embedding endpoint, or chat model;
2. an opt-in integration test calls the already-running local API and thereby
   exercises the configured pgvector, embedding, and chat services.

## Unit test suite

Run the unit suite from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ -q
```

The suite must remain independent of live services. `tests/conftest.py` sets
test-only Qdrant and model values before the application modules load, while
service and HTTP clients are mocked at their adapters.

| Test module | Summary |
| --- | --- |
| `test_api.py` | Validates `/health` and `/chat` HTTP contracts using FastAPI's in-process ASGI transport and mocked chat services. |
| `test_chat_client.py` | Verifies the OpenAI-compatible chat request shape, response parsing, token limit, and thinking control using mocked HTTP transport. |
| `test_chunker.py` | Covers text and Markdown chunking, deterministic IDs, source-path preservation, sections, and metadata propagation. |
| `test_chunk_ids.py` | Covers deterministic and distinct document/chunk ID generation. |
| `test_code_ingestion.py` | Covers Python and Kotlin loader metadata plus parser-aware Python symbols and line ranges. |
| `test_domain_models.py` | Checks that the ingestion model emits the top-level chunk ID expected by vector-store adapters. |
| `test_java_code_chunker.py` | Covers Java type/member symbol extraction and fallback behavior for malformed Java. |
| `test_loaders.py` | Covers text, Markdown, HTML, directory loading, unsupported/missing files, file-size limits, and Java discovery exclusions. |
| `test_services.py` | Covers retrieval orchestration, chat grounding/abstention, provider separation, debug metadata, and hybrid reciprocal-rank fusion. |
| `test_workspace_authorization.py` | Covers workspace discovery, authorization-before-chat, principal propagation, session-scope mismatch rejection, and two-user isolation through FastAPI dependency overrides. |

On Windows, use a unique repository-local base temporary directory if the
default `%TEMP%` pytest directory is not accessible:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ --ignore=tests\integration -q -p no:cacheprovider --basetemp=.codex-test-tmp-local
```

## Live integration test

`tests/integration/test_live_stack.py` is deliberately skipped unless enabled.
It does not start the application. Instead, it calls the API you already run
from IntelliJ at `RAG_API_BASE_URL` (default `http://127.0.0.1:8000`).

The test discovers an authorized workspace and creates a temporary Markdown fixture, then:

1. confirms API readiness and the PostgreSQL/pgvector configuration;
2. ingests the fixture through `POST /ingest`, which calls the configured
   embedding endpoint and pgvector;
3. asks a grounded question through `POST /chat` and verifies a source from
   that fixture is returned;
4. requests a non-member workspace and verifies that authorization rejects it;
5. re-ingests the now-empty fixture directory to remove its indexed document.

Run it only when the app, model endpoints, and PostgreSQL/pgvector are ready:

```powershell
$env:RUN_LIVE_INTEGRATION = "1"
$env:RAG_API_BASE_URL = "http://127.0.0.1:8000" # optional when using the default
.\.venv\Scripts\python.exe -m pytest tests\integration\ -q --basetemp .pytest-integration-tmp
Remove-Item Env:RUN_LIVE_INTEGRATION
```

For PyCharm, use a Pytest configuration with the repository `.venv`, working
directory set to the project root, and these environment variables:

```text
RUN_LIVE_INTEGRATION=1
RAG_API_BASE_URL=http://127.0.0.1:8000
```

Set its additional arguments to `--basetemp .pytest-integration-tmp`. This
uses a stable project-local temporary directory and avoids Windows cleanup
noise from pytest's `%TEMP%` directory. The test cleans its indexed data before
it finishes. If it is interrupted during cleanup, any stale data is isolated
by its unique workspace ID.

## Indexing this guide

After changing this document, index it with the running API so it becomes
available to RAG chat in the default workspace:

```powershell
$body = @{ source_path = (Resolve-Path .\docs\testing.md).Path; recursive = $false } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/ingest" -ContentType "application/json" -Body $body
```
