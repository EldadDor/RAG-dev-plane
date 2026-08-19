"""Opt-in end-to-end verification against an already-running RAG service."""

from __future__ import annotations

import os
from uuid import uuid4

import httpx
import pytest


RUN_LIVE_INTEGRATION = os.getenv("RUN_LIVE_INTEGRATION") == "1"
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not RUN_LIVE_INTEGRATION,
        reason="Set RUN_LIVE_INTEGRATION=1 to call the running RAG API and live dependencies.",
    ),
]


def test_live_stack_ingests_retrieves_and_isolates_workspace(tmp_path):
    """Exercise API ingestion, pgvector retrieval, embeddings, and chat grounding."""
    api_base_url = os.getenv("RAG_API_BASE_URL", "http://127.0.0.1:8000")
    workspace_id = f"integration-{uuid4().hex}"
    isolated_workspace_id = f"integration-empty-{uuid4().hex}"
    source_dir = tmp_path / "live-stack-fixture"
    source_dir.mkdir()
    source_file = source_dir / "release-note.md"
    unique_fact = "Project Aurora uses the retrieval sentinel named copper-otter-914."
    source_file.write_text(f"# Integration fixture\n\n{unique_fact}\n", encoding="utf-8")

    with httpx.Client(base_url=api_base_url, timeout=180.0) as client:
        try:
            readiness = client.get("/readiness")
            assert readiness.status_code == 200, readiness.text
            readiness_data = readiness.json()
            assert readiness_data["status"] == "ok", readiness_data
            assert readiness_data["vector_store"] == "ok", readiness_data
            assert readiness_data["details"]["vector_store_type"] == "postgres", readiness_data

            ingestion = client.post(
                "/ingest",
                json={
                    "source_path": str(source_dir),
                    "recursive": True,
                    "workspace_id": workspace_id,
                },
            )
            assert ingestion.status_code == 200, ingestion.text
            assert ingestion.json()["indexed"] >= 1

            response = client.post(
                "/chat",
                json={
                    "question": "What is the retrieval sentinel used by Project Aurora?",
                    "workspace_id": workspace_id,
                    "top_k": 3,
                },
            )
            assert response.status_code == 200, response.text
            answer = response.json()
            assert answer["grounded"] is True
            assert answer["sources"]
            assert any(item["source_path"] == str(source_file) for item in answer["sources"])

            isolated_response = client.post(
                "/chat",
                json={
                    "question": "What is the retrieval sentinel used by Project Aurora?",
                    "workspace_id": isolated_workspace_id,
                    "top_k": 3,
                },
            )
            assert isolated_response.status_code == 200, isolated_response.text
            isolated_answer = isolated_response.json()
            assert isolated_answer["grounded"] is False
            assert isolated_answer["sources"] == []
        finally:
            source_file.unlink(missing_ok=True)
            cleanup = client.post(
                "/ingest",
                json={
                    "source_path": str(source_dir),
                    "recursive": True,
                    "workspace_id": workspace_id,
                },
            )
            assert cleanup.status_code == 200, cleanup.text
