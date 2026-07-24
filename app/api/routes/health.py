from fastapi import APIRouter

from app.config.settings import get_settings
from app.services.vector_store import get_vector_store


router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    settings = get_settings()
    vector_store = get_vector_store()
    qdrant_reachable = vector_store.ping()
    return {
        "status": "ok" if qdrant_reachable else "degraded",
        "app_name": "AI Knowledge Base",
        "collection": settings.qdrant_collection,
        "qdrant_reachable": qdrant_reachable,
        "collection_exists": vector_store.collection_exists(),
        "openai_configured": bool(settings.openai_api_key),
    }
