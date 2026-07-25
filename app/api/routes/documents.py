from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config.settings import get_settings
from app.models.schemas import (
    BulkIngestResponse,
    DocumentDeleteRequest,
    DocumentDeleteResponse,
    DocumentFilterOptionsResponse,
    DocumentIngestRequest,
    DocumentIngestResponse,
    DocumentListResponse,
    SystemOverviewResponse,
)
from app.services.document_loader import SUPPORTED_SUFFIXES, is_supported_file
from app.services.rag_service import get_rag_service
from app.services.vector_store import get_vector_store


router = APIRouter(prefix="/documents", tags=["documents"])
SAFE_LABEL_PATTERN = re.compile(r"[^\w\u4e00-\u9fff\- ]+", re.UNICODE)


@router.get("", response_model=DocumentListResponse)
def list_documents() -> DocumentListResponse:
    return DocumentListResponse(documents=_build_document_inventory())


@router.get("/filters", response_model=DocumentFilterOptionsResponse)
def get_filter_options() -> DocumentFilterOptionsResponse:
    documents = _build_document_inventory()
    return DocumentFilterOptionsResponse(
        categories=sorted({item["category"] for item in documents}),
        source_labels=sorted({item["source_label"] for item in documents}),
        file_types=sorted({item["file_type"] for item in documents}),
        storage_areas=sorted({item["storage_area"] for item in documents}),
        statuses=sorted({item["status"] for item in documents}),
    )


@router.get("/overview", response_model=SystemOverviewResponse)
def get_system_overview() -> SystemOverviewResponse:
    settings = get_settings()
    documents = _build_document_inventory()
    vector_store = get_vector_store()
    qdrant_reachable = vector_store.ping()

    indexed_documents = sum(1 for item in documents if item["indexed"])
    pending_documents = sum(1 for item in documents if item["status"] == "pending_index")
    orphaned_documents = sum(1 for item in documents if item["status"] == "orphaned_index")
    external_indexed_documents = sum(1 for item in documents if item["status"] == "external_index")
    total_chunks = vector_store.count_points() if qdrant_reachable else sum(item["chunk_count"] for item in documents)

    return SystemOverviewResponse(
        status="ok" if qdrant_reachable else "degraded",
        app_name="AI Knowledge Base",
        collection=settings.qdrant_collection,
        qdrant_reachable=qdrant_reachable,
        collection_exists=vector_store.collection_exists(),
        openai_configured=bool(settings.openai_api_key),
        raw_data_dir=str(Path(settings.raw_data_dir).resolve()),
        upload_dir=str(Path(settings.upload_dir).resolve()),
        supported_file_types=sorted(suffix.lstrip(".") for suffix in SUPPORTED_SUFFIXES),
        total_documents=len(documents),
        indexed_documents=indexed_documents,
        pending_documents=pending_documents,
        orphaned_documents=orphaned_documents,
        external_indexed_documents=external_indexed_documents,
        total_chunks=total_chunks,
        categories=sorted({item["category"] for item in documents}),
        source_labels=sorted({item["source_label"] for item in documents}),
        storage_areas=sorted({item["storage_area"] for item in documents}),
    )


@router.post("/ingest/raw", response_model=BulkIngestResponse)
def ingest_raw_documents() -> BulkIngestResponse:
    service = get_rag_service()
    summaries = service.ingest_raw_directory()
    normalized = [DocumentIngestResponse(**summary) for summary in summaries]
    return BulkIngestResponse(ingested_count=len(normalized), summaries=normalized)


@router.post("/upload", response_model=DocumentIngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    source_label: str = Form(default="upload"),
    category: str = Form(default="general"),
) -> DocumentIngestResponse:
    settings = get_settings()
    filename = Path(file.filename or "").name
    if not filename:
        raise HTTPException(status_code=400, detail="文件名不能为空。")

    destination = Path(settings.upload_dir) / _sanitize_label(category, default="general") / filename
    if not is_supported_file(destination):
        raise HTTPException(
            status_code=400,
            detail=f"仅支持以下文件类型：{', '.join(sorted(suffix.lstrip('.') for suffix in SUPPORTED_SUFFIXES))}",
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(await file.read())

    service = get_rag_service()
    summary = service.ingest_file(
        destination,
        source_label=_sanitize_label(source_label, default="upload"),
        category=_sanitize_label(category, default="general"),
    )
    return DocumentIngestResponse(**summary)


@router.post("/ingest", response_model=DocumentIngestResponse)
def ingest_document(request: DocumentIngestRequest) -> DocumentIngestResponse:
    path = Path(request.path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if not is_supported_file(path):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    service = get_rag_service()
    summary = service.ingest_file(
        path,
        source_label=_sanitize_label(request.source_label, default="manual"),
        category=_sanitize_label(request.category, default=path.parent.name or "general"),
    )
    return DocumentIngestResponse(**summary)


@router.post("/delete", response_model=DocumentDeleteResponse)
def delete_document(request: DocumentDeleteRequest) -> DocumentDeleteResponse:
    settings = get_settings()
    storage_roots = {
        "raw": Path(settings.raw_data_dir).resolve(),
        "upload": Path(settings.upload_dir).resolve(),
    }
    if request.storage_area not in storage_roots:
        raise HTTPException(status_code=400, detail="storage_area must be raw or upload")

    target = (storage_roots[request.storage_area] / request.relative_path).resolve()
    if storage_roots[request.storage_area] not in target.parents and target != storage_roots[request.storage_area]:
        raise HTTPException(status_code=400, detail="Invalid relative_path")

    deleted_file = False
    if request.delete_file and target.exists() and target.is_file():
        target.unlink()
        deleted_file = True

    deleted_points = 0
    if request.delete_index:
        deleted_points = get_vector_store().delete_by_file_path(str(target))

    deleted_index = deleted_points > 0
    if not deleted_file and not deleted_index:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentDeleteResponse(
        filename=target.name,
        deleted_file=deleted_file,
        deleted_index=deleted_index,
        deleted_points=deleted_points,
        message="删除完成。",
    )


def _build_document_inventory() -> list[dict]:
    settings = get_settings()
    raw_dir = Path(settings.raw_data_dir).resolve()
    upload_dir = Path(settings.upload_dir).resolve()

    documents: dict[str, dict] = {}
    _collect_disk_documents(documents, raw_dir, "raw")
    _collect_disk_documents(documents, upload_dir, "upload")

    vector_store = get_vector_store()
    for item in vector_store.list_indexed_documents():
        file_path = str(Path(item["file_path"]).resolve())
        existing = documents.get(file_path)
        if existing is None:
            guessed = _guess_storage_area(file_path, raw_dir, upload_dir)
            relative_path = _relative_path_for_display(file_path, guessed, raw_dir, upload_dir)
            exists_on_disk = Path(file_path).exists()
            documents[file_path] = {
                "filename": item["filename"],
                "relative_path": relative_path,
                "size_bytes": None,
                "file_type": item["file_type"] or _suffix_to_file_type(Path(file_path).suffix),
                "category": item["category"],
                "source_label": item["source_label"],
                "storage_area": guessed,
                "indexed": True,
                "chunk_count": item["chunk_count"],
                "exists_on_disk": exists_on_disk,
                "updated_at": item.get("updated_at"),
                "status": "external_index" if guessed == "unknown" else "orphaned_index",
            }
            continue

        existing["indexed"] = True
        existing["chunk_count"] = item["chunk_count"]
        existing["source_label"] = item["source_label"] or existing["source_label"]
        existing["category"] = item["category"] or existing["category"]
        existing["file_type"] = item["file_type"] or existing["file_type"]
        existing["updated_at"] = existing["updated_at"] or item.get("updated_at")
        existing["status"] = "indexed"

    return [documents[key] for key in sorted(documents.keys())]


def _collect_disk_documents(documents: dict[str, dict], base_dir: Path, storage_area: str) -> None:
    if not base_dir.exists():
        return

    for path in sorted(base_dir.rglob("*")):
        if not path.is_file() or not is_supported_file(path):
            continue
        resolved = str(path.resolve())
        stat = path.stat()
        documents[resolved] = {
            "filename": path.name,
            "relative_path": str(path.relative_to(base_dir)),
            "size_bytes": stat.st_size,
            "file_type": _suffix_to_file_type(path.suffix),
            "category": _infer_category(base_dir, path),
            "source_label": storage_area,
            "storage_area": storage_area,
            "indexed": False,
            "chunk_count": 0,
            "exists_on_disk": True,
            "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            "status": "pending_index",
        }


def _infer_category(base_dir: Path, path: Path) -> str:
    relative = path.relative_to(base_dir)
    if len(relative.parts) <= 1:
        return "general"
    return relative.parts[0]


def _guess_storage_area(file_path: str, raw_dir: Path, upload_dir: Path) -> str:
    resolved = Path(file_path)
    try:
        resolved.relative_to(raw_dir)
        return "raw"
    except ValueError:
        pass
    try:
        resolved.relative_to(upload_dir)
        return "upload"
    except ValueError:
        return "unknown"


def _relative_path_for_display(file_path: str, storage_area: str, raw_dir: Path, upload_dir: Path) -> str:
    resolved = Path(file_path)
    try:
        if storage_area == "raw":
            return str(resolved.relative_to(raw_dir))
        if storage_area == "upload":
            return str(resolved.relative_to(upload_dir))
    except ValueError:
        pass
    return resolved.name


def _sanitize_label(value: str | None, default: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        return default
    normalized = normalized.replace("\\", " ").replace("/", " ")
    normalized = SAFE_LABEL_PATTERN.sub(" ", normalized)
    normalized = " ".join(normalized.split())
    return normalized or default


def _suffix_to_file_type(suffix: str) -> str:
    return suffix.lower().lstrip(".") or "unknown"
