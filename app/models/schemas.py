from typing import Any

from pydantic import BaseModel, Field


class DocumentIngestRequest(BaseModel):
    path: str = Field(description="Absolute or project-relative path to a document.")
    source_label: str = Field(default="manual", description="Logical source label for metadata.")
    category: str | None = Field(default=None, description="Optional category label.")


class DocumentIngestResponse(BaseModel):
    filename: str
    chunks_created: int
    points_written: int
    source_label: str
    category: str | None = None


class BulkIngestResponse(BaseModel):
    ingested_count: int
    summaries: list[DocumentIngestResponse]


class ManagedDocumentItem(BaseModel):
    filename: str
    relative_path: str
    size_bytes: int | None = None
    category: str
    source_label: str
    storage_area: str
    indexed: bool
    chunk_count: int
    exists_on_disk: bool


class DocumentListResponse(BaseModel):
    documents: list[ManagedDocumentItem]


class SystemOverviewResponse(BaseModel):
    status: str
    app_name: str
    collection: str
    qdrant_reachable: bool
    collection_exists: bool
    openai_configured: bool
    raw_data_dir: str
    upload_dir: str
    total_documents: int
    indexed_documents: int
    total_chunks: int
    categories: list[str]
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
    message: str


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
