from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.query import router as query_router
from app.config.settings import get_settings
from app.services.rag_service import get_rag_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.auto_ingest_on_startup:
        raw_dir = Path(settings.raw_data_dir)
        raw_dir.mkdir(parents=True, exist_ok=True)
        service = get_rag_service()
        service.ingest_directory(
            raw_dir,
            source_label=settings.auto_ingest_source_label,
        )
    yield


app = FastAPI(
    title="AI Knowledge Base",
    version="0.1.0",
    description="Personal RAG knowledge base for document search and question answering.",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(documents_router, prefix="/api")
app.include_router(query_router, prefix="/api")
