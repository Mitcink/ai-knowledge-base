from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


DocumentStatus = Literal["indexed", "pending_index", "orphaned_index", "external_index"]


class DocumentIngestRequest(BaseModel):
    path: str = Field(description="Absolute or project-relative path to a document.")
    source_label: str = Field(default="manual", description="Logical source label for metadata.")
    category: str | None = Field(default=None, description="Optional category label.")


class DocumentIngestResponse(BaseModel):
    filename: str
    file_type: str
    chunks_created: int
    points_written: int
    source_label: str
    category: str | None = None
    message: str


class BulkIngestResponse(BaseModel):
    ingested_count: int
    summaries: list[DocumentIngestResponse]


class ManagedDocumentItem(BaseModel):
    filename: str
    relative_path: str
    size_bytes: int | None = None
    file_type: str
    category: str
    source_label: str
    storage_area: str
    indexed: bool
    chunk_count: int
    exists_on_disk: bool
    updated_at: str | None = None
    status: DocumentStatus


class DocumentListResponse(BaseModel):
    documents: list[ManagedDocumentItem]


class DocumentFilterOptionsResponse(BaseModel):
    categories: list[str]
    source_labels: list[str]
    file_types: list[str]
    storage_areas: list[str]
    statuses: list[DocumentStatus]


class SystemOverviewResponse(BaseModel):
    status: str
    app_name: str
    collection: str
    qdrant_reachable: bool
    collection_exists: bool
    openai_configured: bool
    raw_data_dir: str
    upload_dir: str
    supported_file_types: list[str]
    total_documents: int
    indexed_documents: int
    pending_documents: int
    orphaned_documents: int
    external_indexed_documents: int
    total_chunks: int
    categories: list[str]
    source_labels: list[str]
    storage_areas: list[str]


class DocumentDeleteRequest(BaseModel):
    storage_area: str = Field(description="raw or upload")
    relative_path: str = Field(description="Path relative to the storage area root")
    delete_file: bool = True
    delete_index: bool = True


class DocumentDeleteResponse(BaseModel):
    filename: str
    deleted_file: bool
    deleted_index: bool
    deleted_points: int = 0
    message: str


class QueryRequest(BaseModel):
    question: str
    top_k: int = Field(default=6, ge=1, le=12)
    category_filter: str | None = None
    source_filter: str | None = None
    file_type_filter: str | None = None
    tag_filter: str | None = None

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("question must not be empty")
        return cleaned


class Citation(BaseModel):
    title: str
    filename: str
    source: str
    file_path: str
    chunk_id: str
    score: float
    excerpt: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    debug: dict[str, Any]
