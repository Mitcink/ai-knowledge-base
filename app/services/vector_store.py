from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.config.settings import get_settings


class VectorStore:
    def __init__(self) -> None:
        settings = get_settings()
        self._collection = settings.qdrant_collection
        self._client = QdrantClient(url=settings.qdrant_url)

    def ping(self) -> bool:
        try:
            self._client.get_collections()
            return True
        except Exception:
            return False

    def ensure_collection(self, vector_size: int) -> None:
        collections = self._client.get_collections().collections
        if any(item.name == self._collection for item in collections):
            return
        self._client.create_collection(
            collection_name=self._collection,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )

    def upsert(self, points: list[models.PointStruct]) -> None:
        self._client.upsert(collection_name=self._collection, points=points)

    def search(self, query_vector: list[float], limit: int, tag_filter: str | None) -> list[dict[str, Any]]:
        query_filter = None
        if tag_filter:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="tags",
                        match=models.MatchValue(value=tag_filter),
                    )
                ]
            )

        results = self._client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
        normalized = []
        for item in results:
            payload = item.payload or {}
            normalized.append(
                {
                    "score": float(item.score),
                    "payload": payload,
                }
            )
        return normalized


_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store

