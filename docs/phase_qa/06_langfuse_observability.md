# Langfuse Observability — Developer Q&A

1. **Is Langfuse enabled by default?** No; `LANGFUSE_ENABLED=false` keeps existing runtime behavior unchanged.
2. **What should a root trace represent?** One API request, correlated with workspace and session metadata.
3. **Which RAG operations deserve nested spans?** Memory, query rewriting, embeddings, semantic/lexical retrieval, and answer generation.
4. **Should raw internal content be exported by default?** No; `LANGFUSE_CAPTURE_CONTENT=false` requires explicit approval for it.
5. **How can Langfuse evaluate RAG quality?** Scores, user feedback, datasets, and experiments can track groundedness and regressions.
