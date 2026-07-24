from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config.settings import get_settings
from app.models.schemas import DocumentIngestRequest, DocumentIngestResponse, DocumentListResponse
from app.services.rag_service import get_rag_service


router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents() -> DocumentListResponse:
    settings = get_settings()
    raw_dir = Path(settings.raw_data_dir)
    documents = []
    for path in sorted(raw_dir.rglob("*")):
        if path.is_file():
            documents.append(
                {
                    "filename": path.name,
                    "relative_path": str(path.relative_to(raw_dir)),
                    "size_bytes": path.stat().st_size,
                    "category": path.parent.name if path.parent != raw_dir else "general",
                }
            )
    return DocumentListResponse(documents=documents)


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
