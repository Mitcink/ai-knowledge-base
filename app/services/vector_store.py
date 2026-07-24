from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.config.settings import get_settings


class VectorStore:
    def __init__(self) -> None:
        settings = get_settings()
        self._collection = settings.qdrant_collection
        self._client = QdrantClient(url=settings.qdrant_url, check_compatibility=False)

    def ping(self) -> bool:
        try:
            self._client.get_collections()
            return True
        except Exception:
            return False

    def collection_exists(self) -> bool:
        try:
            collections = self._client.get_collections().collections
        except Exception:
            return False
        return any(item.name == self._collection for item in collections)

    def ensure_collection(self, vector_size: int) -> None:
        if self.collection_exists():
            return
        self._client.create_collection(
            collection_name=self._collection,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )

    def upsert(self, points: list[models.PointStruct]) -> None:
        self._client.upsert(collection_name=self._collection, points=points)

    def search(
        self,
        query_vector: list[float],
        limit: int,
        category_filter: str | None = None,
        tag_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        if not self.collection_exists():
            return []

        must_conditions: list[models.FieldCondition] = []
        if category_filter:
            must_conditions.append(
                models.FieldCondition(
                    key="category",
                    match=models.MatchValue(value=category_filter),
                )
            )
        if tag_filter:
            must_conditions.append(
                models.FieldCondition(
                    key="tags",
                    match=models.MatchValue(value=tag_filter),
                )
            )

        query_filter = models.Filter(must=must_conditions) if must_conditions else None

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

    def list_indexed_documents(self) -> list[dict[str, Any]]:
        if not self.collection_exists():
            return []

        documents: dict[str, dict[str, Any]] = {}
        next_offset = None
        while True:
            points, next_offset = self._client.scroll(
                collection_name=self._collection,
                limit=256,
                offset=next_offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in points:
                payload = point.payload or {}
                file_path = str(payload.get("file_path", "")).strip()
                if not file_path:
                    continue
                entry = documents.setdefault(
                    file_path,
                    {
                        "file_path": file_path,
                        "filename": file_path.replace("\\", "/").split("/")[-1],
                        "title": payload.get("title", ""),
                        "source_label": str(payload.get("source", "manual")),
                        "category": str(payload.get("category", "general")),
                        "chunk_count": 0,
                    },
                )
                entry["chunk_count"] += 1
            if next_offset is None:
                break

        return sorted(documents.values(), key=lambda item: item["file_path"])

    def delete_by_file_path(self, file_path: str) -> None:
        if not self.collection_exists():
            return
        self._client.delete(
            collection_name=self._collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="file_path",
                            match=models.MatchValue(value=file_path),
                        )
                    ]
                )
            ),
            wait=True,
        )

    def count_points(self) -> int:
        if not self.collection_exists():
            return 0
        return int(self._client.count(collection_name=self._collection, exact=True).count)


_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
