from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)
    include_debug: bool = False
    session_id: str | None = None
    workspace_id: str | None = Field(default=None, min_length=1)


class ChatResponse(BaseModel):
    answer: str
    sources: list["SourceReference"]
    grounded: bool
    session_id: str | None = None
    debug: dict | None = None


class ChatSessionSummary(BaseModel):
    session_id: str
    workspace_id: str
    title: str
    last_preview: str | None = None
    updated_at: str | None = None


class ChatSessionDetail(ChatSessionSummary):
    summary: str | None = None
    turns: list[dict[str, str]] = Field(default_factory=list)


class RenameChatSessionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class PrincipalSummary(BaseModel):
    display_name: str


class WorkspaceSummary(BaseModel):
    workspace_id: str
    display_name: str
    role: str


class WorkspaceListResponse(BaseModel):
    principal: PrincipalSummary
    workspaces: list[WorkspaceSummary]


class SourceReference(BaseModel):
    doc_id: str
    chunk_id: str
    source_path: str
    title: str | None = None
    page: int | None = None
    section: str | None = None
    score: float
    snippet: str


class IngestRequest(BaseModel):
    source_path: str = Field(min_length=1)
    recursive: bool = False
    workspace_id: str | None = Field(default=None, min_length=1)


class IngestResult(BaseModel):
    doc_id: str
    source_path: str
    chunks_indexed: int
    skipped: bool = False
    skip_reason: str | None = None


class IngestResponse(BaseModel):
    indexed: int
    documents: list[IngestResult]


class HealthResponse(BaseModel):
    status: str
    environment: str


class ReadinessResponse(BaseModel):
    status: str
    vector_store: str
    details: dict
