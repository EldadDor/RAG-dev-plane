# Architecture and Kotlin — Developer Q&A

1. **What is the default persistence model?** pgvector chunks, source lifecycle records, and durable conversation tables in PostgreSQL.
2. **How is Kotlin chunked?** Tree-sitter extracts declaration-aware type/function chunks with line ranges.
3. **What does `enclosing_symbol` represent?** The containing declaration, such as a class for a function.
4. **What is deferred for Kotlin?** Broader parser coverage can be extended after real retrieval feedback.
5. **Where is the current phase decision recorded?** `docs/work_current_phase.md` and `docs/next_phase.md`.
