from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4096)
    top_k: int | None = Field(default=None, ge=1, le=50)
    debug: bool = Field(default=False)


class SourceReference(BaseModel):
    doc_id: str
    chunk_id: str
    source_path: str
    title: str | None = None
    page: int | None = None
    section: str | None = None
    score: float
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
    grounded: bool
    debug: dict | None = None


class IngestRequest(BaseModel):
    source_path: str = Field(..., description="File path or directory to ingest")
    recursive: bool = Field(default=False, description="Recurse into subdirectories")
    overwrite: bool = Field(default=True, description="Re-ingest existing documents")


class IngestResult(BaseModel):
    doc_id: str
    source_path: str
    chunks_indexed: int
    skipped: bool = False
    skip_reason: str | None = None


class IngestResponse(BaseModel):
    indexed: int = Field(description="Total chunks indexed")
    documents: list[IngestResult]


class HealthResponse(BaseModel):
    status: str
    environment: str


class ReadinessResponse(BaseModel):
    status: str
    qdrant: str
    details: dict | None = None
