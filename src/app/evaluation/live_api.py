from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.domain.models import RetrievedChunk
from app.evaluation.models import GoldenCase


class LiveApiBenchmarkClient:
    """Minimal `/chat` adapter used only by the opt-in local benchmark CLI."""

    def __init__(self, client: httpx.AsyncClient, workspace_id: str | None = None,
                 model_profile: str | None = None, chunking_profile: str | None = None) -> None:
        self._client = client
        self._workspace_id = workspace_id
        self._model_profile = model_profile
        self._chunking_profile = chunking_profile
        self._responses: dict[tuple, dict[str, Any]] = {}
        self.response_records: list[dict[str, Any]] = []
        self._scope_capability_checked = False

    async def _check_scope_capability(self) -> None:
        if self._scope_capability_checked:
            return
        response = await self._client.get("/openapi.json")
        response.raise_for_status()
        spec = response.json()
        schema = spec["paths"]["/chat"]["post"]["requestBody"]["content"]["application/json"]["schema"]
        if "$ref" in schema:
            for part in schema["$ref"].removeprefix("#/").split("/"):
                spec = spec[part]
            schema = spec
        if "document_id" not in schema.get("properties", {}):
            raise ValueError("API does not advertise document-scoped chat")
        self._scope_capability_checked = True

    def _key(self, question: str, workspace_id: str | None, chunking_profile: str | None, top_k: int, document_id: str | None = None) -> tuple:
        return question, workspace_id or self._workspace_id, chunking_profile or self._chunking_profile, top_k, document_id

    async def _chat(self, case: GoldenCase, top_k: int) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "question": case.question,
            "top_k": top_k,
            "include_debug": True,
        }
        if case.workspace_id or self._workspace_id:
            payload["workspace_id"] = case.workspace_id or self._workspace_id
        if case.chunking_profile or self._chunking_profile:
            payload["chunking_profile"] = case.chunking_profile or self._chunking_profile
        if self._model_profile:
            payload["model_profile"] = self._model_profile
        if case.document_id is not None:
            await self._check_scope_capability()
            payload["document_id"] = case.document_id
        response = await self._client.post("/chat", json=payload)
        try:
            body = response.json()
        except ValueError:
            self.response_records.append({"request": payload, "status_code": response.status_code, "error": "Non-JSON response"})
            raise
        self.response_records.append({"request": payload, "status_code": response.status_code, "response": body})
        response.raise_for_status()
        if not isinstance(body, dict) or not isinstance(body.get("answer"), str) or not body["answer"].strip() or not isinstance(body.get("sources"), list):
            raise ValueError("Malformed chat benchmark response")
        if case.document_id is not None:
            if type(body.get("grounded")) is not bool:
                raise ValueError("Malformed scoped chat grounded state")
            if body.get("session_id", "missing") is not None:
                raise ValueError("Scoped chat response must be stateless")
            if any(not isinstance(s, dict) or s.get("doc_id") != case.document_id for s in body["sources"]):
                raise ValueError("Out-of-scope chat citation")
        self._responses[self._key(case.question, case.workspace_id, case.chunking_profile, top_k, case.document_id)] = body
        return body

    async def retrieve(self, question: str, top_k: int | None = None, workspace_id: str | None = None, chunking_profile: str | None = None, document_id: str | None = None) -> list[RetrievedChunk]:
        case = GoldenCase(
            case_id="retrieval-probe", question=question, expected_facts=("benchmark probe",),
            workspace_id=workspace_id, chunking_profile=chunking_profile, document_id=document_id,
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
            response = self._responses.get(self._key(case.question, case.workspace_id, case.chunking_profile, top_k, case.document_id))
            if response is None:
                response = await self._chat(case, top_k)
            return response["answer"]
        return answer
