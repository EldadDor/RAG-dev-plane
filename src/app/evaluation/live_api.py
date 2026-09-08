from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.domain.models import RetrievedChunk
from app.evaluation.models import GoldenCase


class LiveApiBenchmarkClient:
    """Minimal `/chat` adapter used only by the opt-in local benchmark CLI."""

    def __init__(self, client: httpx.AsyncClient, workspace_id: str | None = None) -> None:
        self._client = client
        self._workspace_id = workspace_id
        self._responses: dict[tuple[str, str | None, str | None, int], dict[str, Any]] = {}

    def _key(self, question: str, workspace_id: str | None, chunking_profile: str | None, top_k: int) -> tuple[str, str | None, str | None, int]:
        return question, workspace_id or self._workspace_id, chunking_profile, top_k

    async def _chat(self, case: GoldenCase, top_k: int) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "question": case.question,
            "top_k": top_k,
            "include_debug": True,
        }
        if case.workspace_id or self._workspace_id:
            payload["workspace_id"] = case.workspace_id or self._workspace_id
        if case.chunking_profile:
            payload["chunking_profile"] = case.chunking_profile
        response = await self._client.post("/chat", json=payload)
        response.raise_for_status()
        body = response.json()
        self._responses[self._key(case.question, case.workspace_id, case.chunking_profile, top_k)] = body
        return body

    async def retrieve(self, question: str, top_k: int | None = None, workspace_id: str | None = None, chunking_profile: str | None = None) -> list[RetrievedChunk]:
        case = GoldenCase(
            case_id="retrieval-probe", question=question, expected_facts=("benchmark probe",),
            workspace_id=workspace_id, chunking_profile=chunking_profile,
        )
        response = await self._chat(case, top_k or 5)
        return [
            RetrievedChunk(
                chunk_id=item["chunk_id"], doc_id=item["doc_id"], source_path=item["source_path"],
                text=item.get("snippet", ""), score=float(item["score"]), title=item.get("title"),
                page=item.get("page"), section=item.get("section"),
            )
            for item in response.get("sources", [])
        ]

    def answer_function(self, top_k: int) -> Callable[[GoldenCase], Awaitable[str]]:
        async def answer(case: GoldenCase) -> str:
            response = self._responses.get(self._key(case.question, case.workspace_id, case.chunking_profile, top_k))
            if response is None:
                response = await self._chat(case, top_k)
            return str(response.get("answer", ""))
        return answer
