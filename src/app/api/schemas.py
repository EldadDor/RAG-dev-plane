from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)
    include_debug: bool = False
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list["SourceReference"]
    grounded: bool
    debug: dict | None = None


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
