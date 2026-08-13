# AGENT.md

## Project context
Python RAG API backed by PostgreSQL + pgvector and local models served through Ollama-compatible endpoints. Qdrant remains supported as an alternative vector store.

## Environment assumptions
- Do **not** start, restart, or stop the application.
- Do **not** run the dev server, uvicorn, Docker Compose, tests that boot the app, or any long-lived process unless explicitly asked.
- Always assume the user is already running the app manually.
- Prefer inspecting code, configs, logs, and making minimal targeted edits.

## Current runtime configuration
- API: `http://0.0.0.0:8000`
- Chat provider: `openai_compatible`
- Chat base URL: `http://localhost:11434/v1`
- Chat model: `qwen2.5:7b-instruct-q4_K_M`
- Embeddings provider: `ollama`
- Embedding base URL: `http://localhost:11434`
- Embedding model: `nomic-embed-text`
- Vector DB: PostgreSQL + pgvector at `10.100.102.12:5432/ragdb`
- Schema/table: `rag.document_chunks`
- Vector dimensions: `768`
- Retrieval: `TOP_K=5`, `CHUNK_SIZE=800`, `CHUNK_OVERLAP=120`, `RERANK_ENABLED=false`

## Working style
- Be concise and practical.
- Before changing code, explain the likely root cause in 1-3 bullets.
- Prefer diffs or small edits over broad refactors.
- Preserve the existing stack and configuration choices unless the user asks otherwise.
- When suggesting commands, provide them for the user to run; do not execute app-running commands yourself.

## Chat endpoint debugging
The user tests chat with:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"How does the ingestion pipeline work?"}'
```

Current observed result:
- Request returns HTTP `502` from `/chat`.

When debugging this flow, prioritize checking:
1. Whether the app's OpenAI-compatible client is calling the correct Ollama endpoint format for `http://localhost:11434/v1`.
2. Whether the configured model name `qwen2.5:7b-instruct-q4_K_M` exactly matches a locally available Ollama model tag.
3. Whether the chat code expects OpenAI `/chat/completions` semantics while Ollama is exposing a slightly different response or auth expectation.
4. Whether the API container/process is running in an environment where `localhost:11434` points to the same machine as Ollama.
5. Whether the app is converting upstream connection/model errors into a generic 502.

## Safe agent tasks
- Read Python source files, config files, and logs.
- Trace the `/chat` request path end to end.
- Validate provider adapters, request payloads, and response parsing.
- Propose exact code changes.
- Add focused logging around upstream chat calls.
- Write curl examples for direct upstream testing.

## Avoid
- Do not assume network topology; verify whether `localhost` is correct for the running process.
- Do not silently change model names, ports, or provider types.
- Do not add unnecessary frameworks or abstractions.
- Do not rewrite working ingestion/retrieval code when the issue is isolated to chat.

## Preferred response format
1. Brief diagnosis.
2. Exact files/functions to inspect.
3. Minimal patch proposal.
4. Verification steps the user can run manually.
