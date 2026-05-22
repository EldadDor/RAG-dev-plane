---
applyTo: "src/**/*retriev*.py,src/**/*vector*.py,src/**/*embed*.py,src/**/*rerank*.py,src/**/*prompt*.py,src/**/*chat*.py,src/**/*query*.py,tests/**/*retriev*.py,tests/**/*chat*.py,tests/**/*prompt*.py"
---

# Retrieval, embedding, and answer instructions

## Current baseline
- Use Qdrant as the vector database.
- Use Ollama for embeddings by default.
- Use `mxbai-embed-large` as the default embedding model.
- Use an OpenAI-compatible chat provider for final answer generation.
- Use `Qwen3-Coder-30B-A3B-Instruct-Q4_K_M` as the default chat model.

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
