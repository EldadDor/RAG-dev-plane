from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)
    include_debug: bool = False
    session_id: str | None = None
    workspace_id: str | None = Field(default=None, min_length=1)
    chunking_profile: str | None = Field(default=None, min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    model_profile: str | None = Field(default=None, min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


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
    updated_at: datetime


class ChatTurnResponse(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ChatSessionDetail(ChatSessionSummary):
    summary: str | None = None
    turns: list[ChatTurnResponse] = Field(default_factory=list)


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


class ApiErrorResponse(BaseModel):
    code: str
    message: str


class AccountProfile(BaseModel):
    display_name: str
    email: str | None


class AccountPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recent_chat_limit: StrictInt

    @field_validator("recent_chat_limit")
    @classmethod
    def supported_limit(cls, value: int) -> int:
        if value not in (10, 20, 50, 100):
            raise ValueError("Unsupported recent-chat limit")
        return value


class AccountPreferenceCapabilities(BaseModel):
    read: bool
    update: bool
    persistence: Literal["server", "process", "unavailable"]
    editable_fields: list[Literal["recent_chat_limit"]]
    recent_chat_limit_options: list[int] = Field(default_factory=lambda: [10, 20, 50, 100])
    recent_chat_limit_default: Literal[10] = 10


class AccountLogoutCapability(BaseModel):
    supported: Literal[False] = False
    reason: Literal["fixed_local_identity", "not_configured"]


class GatewayLogoutCapability(BaseModel):
    supported: Literal[True] = True
    owner: Literal["gateway"] = "gateway"
    method: Literal["POST"] = "POST"
    url: Literal["/auth/logout"] = "/auth/logout"
    scope: Literal["application"] = "application"


class AccountCapabilities(BaseModel):
    profile_editable: Literal[False] = False
    preferences: AccountPreferenceCapabilities
    logout: AccountLogoutCapability | GatewayLogoutCapability


class AccountProfileResponse(BaseModel):
    profile: AccountProfile
    workspaces: list[WorkspaceSummary]
    capabilities: AccountCapabilities


class AccountPreferencesResponse(BaseModel):
    preferences: AccountPreferences
    persistence: Literal["server", "process"]


class DocumentScope(BaseModel):
    model_profile: str
    chunking_profile: str


class DocumentSummary(BaseModel):
    doc_id: str
    title: str = Field(min_length=1, max_length=300)
    file_name: str = Field(min_length=1, max_length=255)
    document_type: Literal["word", "powerpoint", "pdf", "markdown", "html", "text", "code", "unknown"]
    last_ingested_at: datetime | None
    indexed_chunk_count: int = Field(ge=0, le=9007199254740991)


class DocumentPage(BaseModel):
    limit: int = Field(ge=1, le=100)
    has_more: bool
    next_cursor: str | None
    list_revision: str
    generated_at: datetime


class DocumentListResponse(BaseModel):
    workspace_id: str
    scope: DocumentScope
    items: list[DocumentSummary]
    page: DocumentPage


class SourceAssetReference(BaseModel):
    asset_id: str
    media_type: str
    width: int | None = None
    height: int | None = None
    alt_text: str | None = None
    caption: str | None = None
    content_url: str | None = None


class SourceReference(BaseModel):
    doc_id: str
    chunk_id: str
    source_path: str
    title: str | None = None
    page: int | None = None
    section: str | None = None
    score: float
    snippet: str
    assets: list[SourceAssetReference] = Field(default_factory=list)


class IngestRequest(BaseModel):
    source_path: str = Field(min_length=1)
    recursive: bool = False
    workspace_id: str | None = Field(default=None, min_length=1)
    chunking_profile: str | None = Field(default=None, min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    model_profile: str | None = Field(default=None, min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    dry_run: bool = False


class IngestResult(BaseModel):
    doc_id: str
    source_path: str
    chunks_indexed: int
    skipped: bool = False
    skip_reason: str | None = None
    assets_found: int = 0


class IngestResponse(BaseModel):
    indexed: int
    chunking_profile: str
    model_profile: str = "default"
    dry_run: bool
    documents: list[IngestResult]


class WarmModelProfileRequest(BaseModel):
    source_model_profile: str = Field(default="default", min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    workspace_id: str | None = Field(default=None, min_length=1)
    dry_run: bool = False


class WarmModelProfileResponse(BaseModel):
    profile_name: str
    source_model_profile: str
    workspace_id: str
    chunks: int
    cache_hits: int
    provider_calls: int
    dry_run: bool


class HealthResponse(BaseModel):
    status: str
    environment: str


class ReadinessResponse(BaseModel):
    status: str
    vector_store: str
    details: dict
