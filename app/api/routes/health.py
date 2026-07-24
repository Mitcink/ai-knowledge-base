from fastapi import APIRouter

from app.config.settings import get_settings
from app.services.vector_store import get_vector_store


router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    settings = get_settings()
    vector_store = get_vector_store()
    return {
        "status": "ok",
        "collection": settings.qdrant_collection,
        "qdrant_reachable": vector_store.ping(),
    }

