from typing import Any

from pydantic import BaseModel, Field


class DocumentIngestRequest(BaseModel):
    path: str = Field(description="Absolute or project-relative path to a document.")
    source_label: str = Field(default="manual", description="Logical source label for metadata.")


class DocumentIngestResponse(BaseModel):
    filename: str
    chunks_created: int
    points_written: int
    source_label: str


class DocumentListItem(BaseModel):
    filename: str
    relative_path: str
    size_bytes: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentListItem]


class QueryRequest(BaseModel):
    question: str
    top_k: int = 6
    tag_filter: str | None = None


class Citation(BaseModel):
    title: str
    source: str
    file_path: str
    chunk_id: str
    score: float
    excerpt: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    debug: dict[str, Any]

