# RAG Dev Plane — Agent Instructions

## Local services

This project depends on local development services that are manually managed by the developer:

- Ollama, including the chat and embedding models
- PostgreSQL with pgvector, running on the developer's laptop
- The backend application, normally run and debugged from IntelliJ

Do not start, stop, restart, configure, pull models for, or otherwise manage Ollama, PostgreSQL/pgvector, Docker Compose, or IntelliJ unless the developer explicitly asks.

Do not assume these services are available.

## Tests and validation

Do not run tests by default.

Tests may require the developer's local Ollama instance and PostgreSQL/pgvector database and can consume local machine resources.

Only run tests, integration tests, Docker Compose, or commands that connect to local services when the developer explicitly requests it.

For code changes, perform static review and reason about correctness. State which tests or checks the developer should run manually.

## Safe default behavior

- Do not modify `.env`, `.env.azure`, secrets, credentials, or local environment configuration unless explicitly requested.
- Do not make network-dependent changes or download models/dependencies unless explicitly requested.
- Keep changes small and focused.
- Before completing a task, summarize changed files and list validation that was not run.