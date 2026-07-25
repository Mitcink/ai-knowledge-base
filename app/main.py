import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.query import router as query_router
from app.config.settings import get_settings
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.auto_ingest_on_startup:
        raw_dir = Path(settings.raw_data_dir)
        raw_dir.mkdir(parents=True, exist_ok=True)
        try:
            service = get_rag_service()
            service.ingest_directory(
                raw_dir,
                source_label=settings.auto_ingest_source_label,
            )
        except Exception:
            logger.exception("Auto ingest on startup failed")
    yield


app = FastAPI(
    title="AI Knowledge Base",
    version="0.1.0",
    description="Personal RAG knowledge base for document search and question answering.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:8765",
        "http://127.0.0.1:8765",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(documents_router, prefix="/api")
app.include_router(query_router, prefix="/api")
