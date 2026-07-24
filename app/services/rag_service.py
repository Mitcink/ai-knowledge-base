from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from openai import OpenAI
from qdrant_client.http import models

from app.config.settings import get_settings
from app.services.chunking import split_text
from app.services.document_loader import is_supported_file, load_document_text
from app.services.embeddings import get_embedding_client
from app.services.vector_store import get_vector_store


class RagService:
    def __init__(self) -> None:
        settings = get_settings()
        self._settings = settings
        self._embedding_client = get_embedding_client()
        self._vector_store = get_vector_store()
        self._llm_client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

    def ingest_directory(
        self,
        directory: Path,
        source_label: str = "batch",
        default_category: str | None = None,
    ) -> list[dict]:
        summaries = []
        for path in sorted(directory.rglob("*")):
            if path.is_file() and is_supported_file(path):
                category = default_category or self._infer_category(directory, path)
                summaries.append(
                    self.ingest_file(
                        path,
                        source_label=source_label,
                        category=category,
                    )
                )
        return summaries

    def ingest_file(
        self,
        path: Path,
        source_label: str = "manual",
        category: str | None = None,
    ) -> dict:
        text = load_document_text(path)
        category = category or path.parent.name or "general"
        chunks = split_text(
            text=text,
            chunk_size=self._settings.max_chunk_size,
            overlap=self._settings.chunk_overlap,
        )
        if not chunks:
            return {
                "filename": path.name,
                "chunks_created": 0,
                "points_written": 0,
                "source_label": source_label,
                "category": category,
            }

        vectors = self._embedding_client.embed_texts([chunk.content for chunk in chunks])
        self._vector_store.ensure_collection(vector_size=len(vectors[0]))

        points: list[models.PointStruct] = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload={
                        "title": path.stem,
                        "source": source_label,
                        "file_path": str(path),
                        "chunk_id": chunk.chunk_id,
                        "text": chunk.content,
                        "category": category,
                        "tags": [source_label, category, path.suffix.lower().lstrip(".")],
                    },
                )
            )
        self._vector_store.upsert(points)
        return {
            "filename": path.name,
            "chunks_created": len(chunks),
            "points_written": len(points),
            "source_label": source_label,
            "category": category,
        }

    def answer_question(self, question: str, top_k: int | None = None, tag_filter: str | None = None) -> dict:
        top_k = top_k or self._settings.top_k
        query_vector = self._embedding_client.embed_query(question)
        candidates = self._vector_store.search(query_vector=query_vector, limit=max(top_k * 3, top_k), tag_filter=tag_filter)
        ranked = self._rerank(question, candidates)[:top_k]

        context_blocks = []
        citations = []
        for item in ranked:
            payload = item["payload"]
            context_blocks.append(
                f"[{payload['title']} | {payload['chunk_id']}]\n{payload['text']}"
            )
            citations.append(
                {
                    "title": payload["title"],
                    "source": payload["source"],
                    "file_path": payload["file_path"],
                    "chunk_id": payload["chunk_id"],
                    "score": round(item["score"], 4),
                    "excerpt": payload["text"][:240],
                }
            )

        answer = self._generate_answer(question, context_blocks)
        return {
            "answer": answer,
            "citations": citations,
            "debug": {
                "retrieved_candidates": len(candidates),
                "returned_citations": len(citations),
                "tag_filter": tag_filter,
            },
        }

    def _rerank(self, question: str, candidates: list[dict]) -> list[dict]:
        question_terms = {term for term in question.lower().split() if term}
        ranked = []
        for item in candidates:
            text = str(item["payload"].get("text", "")).lower()
            overlap = sum(1 for term in question_terms if term in text)
            adjusted_score = float(item["score"]) + overlap * 0.03
            ranked.append({"score": adjusted_score, "payload": item["payload"]})
        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked

    def _generate_answer(self, question: str, context_blocks: list[str]) -> str:
        context = "\n\n".join(context_blocks) if context_blocks else "No relevant context found."
        prompt = (
            "You are answering based only on the provided knowledge base context. "
            "If the answer is uncertain, say what is missing. "
            "Keep the answer concise and practical.\n\n"
            f"Question:\n{question}\n\n"
            f"Context:\n{context}"
        )
        response = self._llm_client.responses.create(
            model=self._settings.llm_model,
            input=prompt,
        )
        return response.output_text

    def _infer_category(self, root_directory: Path, path: Path) -> str:
        try:
            relative_parent = path.parent.relative_to(root_directory)
        except ValueError:
            return path.parent.name or "general"
        if not relative_parent.parts:
            return "general"
        return relative_parent.parts[0]


_rag_service: RagService | None = None


def get_rag_service() -> RagService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RagService()
    return _rag_service
