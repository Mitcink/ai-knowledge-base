from fastapi import FastAPI

from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.query import router as query_router


app = FastAPI(
    title="AI Knowledge Base",
    version="0.1.0",
    description="Personal RAG knowledge base for document search and question answering.",
)

app.include_router(health_router)
app.include_router(documents_router, prefix="/api")
app.include_router(query_router, prefix="/api")

