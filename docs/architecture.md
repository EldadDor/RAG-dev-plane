# Architecture

## Overview
This starter provides a baseline FastAPI service for a developer-facing RAG application. It separates API routes, typed configuration, domain models, provider clients, retrieval orchestration, chat orchestration, and ingestion logic.

## Request flow
1. `/chat` receives a `ChatRequest`.
2. `ChatService` calls `RetrievalService`.
3. `RetrievalService` creates a query embedding and queries the configured vector store (PostgreSQL + pgvector by default; Qdrant still supported).
4. Retrieved chunks are assembled into a grounded prompt.
5. The OpenAI-compatible chat client generates an answer.
6. The API returns the answer plus structured source references.

## Gaps to implement next
- Real document loaders for markdown, HTML, PDF, and text.
- Collection/table creation and indexing workflows.
- Better chunking strategies beyond fixed-size overlap.
- Optional reranking.
- More complete debug tracing and observability.
