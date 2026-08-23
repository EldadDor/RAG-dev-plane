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


def test_live_stack_ingests_retrieves_and_enforces_workspace_access(tmp_path):
    """Exercise discovery, ingestion, pgvector retrieval, grounding, and authorization."""
    api_base_url = os.getenv("RAG_API_BASE_URL", "http://127.0.0.1:8000")
    requested_workspace_id = os.getenv("RAG_TEST_WORKSPACE_ID")
    workspace_id = requested_workspace_id or ""
    unauthorized_workspace_id = f"integration-unauthorized-{uuid4().hex}"
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

            discovery = client.get("/workspaces")
            assert discovery.status_code == 200, discovery.text
            authorized = discovery.json()["workspaces"]
            assert authorized, "The integration principal has no authorized workspaces"
            workspace_id = requested_workspace_id or authorized[0]["workspace_id"]
            assert workspace_id in {item["workspace_id"] for item in authorized}

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

            unauthorized_response = client.post(
                "/chat",
                json={
                    "question": "What is the retrieval sentinel used by Project Aurora?",
                    "workspace_id": unauthorized_workspace_id,
                    "top_k": 3,
                },
            )
            assert unauthorized_response.status_code == 403, unauthorized_response.text
        finally:
            source_file.unlink(missing_ok=True)
            if workspace_id:
                cleanup = client.post(
                    "/ingest",
                    json={
                        "source_path": str(source_dir),
                        "recursive": True,
                        "workspace_id": workspace_id,
                    },
                )
                assert cleanup.status_code == 200, cleanup.text
