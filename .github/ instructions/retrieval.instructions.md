---
applyTo: "src/**/*retriev*.py,src/**/*vector*.py,src/**/*embed*.py,src/**/*rerank*.py,src/**/*prompt*.py,src/**/*chat*.py,src/**/*query*.py,tests/**/*retriev*.py,tests/**/*chat*.py,tests/**/*prompt*.py"
---

# Retrieval, embedding, and answer instructions

## Current baseline
- Use PostgreSQL + pgvector as the default vector database (matches RAG_Embabel-AI local profile).
- Qdrant remains supported as an alternative vector store.
- Use Ollama for embeddings by default.
- Use `nomic-embed-text` as the default local embedding model (768 dimensions).
- Use an OpenAI-compatible chat provider for final answer generation.
- Use `qwen2.5:7b-instruct-q4_K_M` as the default chat model.

## Implementation rules
- Keep embedding generation and chat generation in separate adapters.
- Retrieval code must depend on the embedding adapter only.
- Chat answer synthesis must depend on the chat adapter only.
- Do not assume the chat endpoint supports embeddings.
- Response payloads must include structured source references.
- Prompt templates must include an abstention instruction.

## Testing rules
- Add tests that verify the embedding client and chat client can be mocked independently.
- Add tests that verify final debug output includes both chat and embedding model metadata where applicable.