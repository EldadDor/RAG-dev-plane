# Code Ingestion and Workspaces — Developer Q&A

1. **Why include `workspace_id` in retrieval?** It prevents evidence from one workspace leaking into another.
2. **How are unchanged sources handled?** A content hash skips re-embedding and re-indexing.
3. **How are deleted files handled on a rescan?** Their stale chunks are removed from the scanned root/workspace.
4. **What metadata is preserved for code?** Language, symbols, line ranges, source path, and repository provenance when available.
5. **How does malformed code behave?** Parser-aware paths fall back to generic chunking instead of failing ingestion.
