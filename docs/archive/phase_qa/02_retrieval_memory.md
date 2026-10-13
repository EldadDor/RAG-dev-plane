# Retrieval and Memory — Developer Q&A

1. **How does hybrid retrieval work?** PostgreSQL semantic and full-text rankings are fused with reciprocal-rank fusion.
2. **Why filter semantic scores?** It prevents weak vector matches from becoming false grounding evidence.
3. **What identifies a conversation?** The `/chat` `session_id`.
4. **Is conversation memory embedded into the document corpus?** No; it remains separate from indexed knowledge.
5. **When is a summary refreshed?** After `MEMORY_SUMMARY_AFTER_TURNS` unsummarized turns.
