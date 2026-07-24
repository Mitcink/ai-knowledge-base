from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config.settings import get_settings
from app.models.schemas import (
    DocumentDeleteRequest,
    DocumentDeleteResponse,
    DocumentIngestRequest,
    DocumentIngestResponse,
    DocumentListResponse,
)
from app.services.rag_service import get_rag_service
from app.services.vector_store import get_vector_store


router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents() -> DocumentListResponse:
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
            documents[file_path] = {
                "filename": item["filename"],
                "relative_path": relative_path,
                "size_bytes": None,
                "category": item["category"],
                "source_label": item["source_label"],
                "storage_area": guessed,
                "indexed": True,
                "chunk_count": item["chunk_count"],
                "exists_on_disk": Path(file_path).exists(),
            }
            continue

        existing["indexed"] = True
        existing["chunk_count"] = item["chunk_count"]
        existing["source_label"] = item["source_label"] or existing["source_label"]
        existing["category"] = item["category"] or existing["category"]

    ordered = [documents[key] for key in sorted(documents.keys())]
    return DocumentListResponse(documents=ordered)


@router.post("/upload", response_model=DocumentIngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    source_label: str = Form(default="upload"),
    category: str = Form(default="general"),
) -> DocumentIngestResponse:
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    category_dir = upload_dir / category
    category_dir.mkdir(parents=True, exist_ok=True)

    destination = category_dir / file.filename
    destination.write_bytes(await file.read())

    service = get_rag_service()
    summary = service.ingest_file(destination, source_label=source_label, category=category)
    return DocumentIngestResponse(**summary)


@router.post("/ingest", response_model=DocumentIngestResponse)
def ingest_document(request: DocumentIngestRequest) -> DocumentIngestResponse:
    path = Path(request.path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    service = get_rag_service()
    summary = service.ingest_file(path, source_label=request.source_label, category=request.category)
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

    deleted_index = False
    if request.delete_index:
        get_vector_store().delete_by_file_path(str(target))
        deleted_index = True

    if not deleted_file and not deleted_index:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentDeleteResponse(
        filename=target.name,
        deleted_file=deleted_file,
        deleted_index=deleted_index,
        message="删除完成",
    )


def _collect_disk_documents(documents: dict[str, dict], base_dir: Path, storage_area: str) -> None:
    if not base_dir.exists():
        return

    for path in sorted(base_dir.rglob("*")):
        if not path.is_file():
            continue
        resolved = str(path.resolve())
        documents[resolved] = {
            "filename": path.name,
            "relative_path": str(path.relative_to(base_dir)),
            "size_bytes": path.stat().st_size,
            "category": _infer_category(base_dir, path),
            "source_label": storage_area,
            "storage_area": storage_area,
            "indexed": False,
            "chunk_count": 0,
            "exists_on_disk": True,
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
