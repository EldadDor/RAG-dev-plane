# Core RAG Foundation — Developer Q&A

1. **Why are chat and embedding clients separate?** The chat provider synthesizes answers; the embedding provider creates retrieval vectors, and either can change independently.
2. **What makes an answer grounded?** It is generated from retrieved chunks and returns structured source references.
3. **What happens with no retrieved evidence?** The service returns an explicit abstention rather than inventing an answer.
4. **What is the default vector store?** PostgreSQL with pgvector; Qdrant is an alternative adapter.
5. **Where are prompts managed?** Centrally in `src/app/prompts`, not embedded in routes or clients.
