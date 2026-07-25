from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from openai import NotFoundError
from openai import OpenAI
from qdrant_client.http import models

from app.config.settings import get_settings
from app.services.chunking import split_text
from app.services.document_loader import is_supported_file, load_document_text
from app.services.embeddings import get_embedding_client
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)


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
                summaries.append(self.ingest_file(path, source_label=source_label, category=category))
        return summaries

    def ingest_file(
        self,
        path: Path,
        source_label: str = "manual",
        category: str | None = None,
    ) -> dict:
        path = path.resolve()
        text = load_document_text(path)
        category = (category or path.parent.name or "general").strip() or "general"
        file_type = path.suffix.lower().lstrip(".")
        chunks = split_text(
            text=text,
            chunk_size=self._settings.max_chunk_size,
            overlap=self._settings.chunk_overlap,
        )
        if not chunks:
            return {
                "filename": path.name,
                "file_type": file_type,
                "chunks_created": 0,
                "points_written": 0,
                "source_label": source_label,
                "category": category,
                "message": "文档内容为空，未写入索引。",
            }

        vectors = self._embedding_client.embed_texts([chunk.content for chunk in chunks])
        self._vector_store.ensure_collection(vector_size=len(vectors[0]))
        self._vector_store.delete_by_file_path(str(path))

        stat = path.stat()
        ingested_at = datetime.now(timezone.utc).isoformat()
        updated_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

        points: list[models.PointStruct] = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload={
                        "title": path.stem,
                        "filename": path.name,
                        "source": source_label,
                        "file_path": str(path),
                        "file_type": file_type,
                        "chunk_id": chunk.chunk_id,
                        "text": chunk.content,
                        "category": category,
                        "updated_at": updated_at,
                        "ingested_at": ingested_at,
                        "tags": [source_label, category, file_type],
                    },
                )
            )
        self._vector_store.upsert(points)
        return {
            "filename": path.name,
            "file_type": file_type,
            "chunks_created": len(chunks),
            "points_written": len(points),
            "source_label": source_label,
            "category": category,
            "message": "文档已完成解析并写入索引。",
        }

    def ingest_raw_directory(self, source_label: str | None = None) -> list[dict]:
        raw_dir = Path(self._settings.raw_data_dir)
        raw_dir.mkdir(parents=True, exist_ok=True)
        return self.ingest_directory(
            raw_dir,
            source_label=source_label or self._settings.auto_ingest_source_label,
        )

    def answer_question(
        self,
        question: str,
        top_k: int | None = None,
        category_filter: str | None = None,
        source_filter: str | None = None,
        file_type_filter: str | None = None,
        tag_filter: str | None = None,
    ) -> dict:
        normalized_question = question.strip()
        if not normalized_question:
            raise ValueError("问题不能为空。")

        top_k = max(1, min(top_k or self._settings.top_k, 12))
        search_limit = max(top_k * 3, top_k)
        query_vector = self._embedding_client.embed_query(normalized_question)
        candidates = self._vector_store.search(
            query_vector=query_vector,
            limit=search_limit,
            category_filter=category_filter,
            source_filter=source_filter,
            file_type_filter=file_type_filter,
            tag_filter=tag_filter,
        )
        ranked = self._rerank(normalized_question, candidates)[:top_k]

        if not ranked:
            return {
                "answer": "没有找到符合当前筛选条件的相关内容。你可以放宽过滤条件，或者先导入更贴近问题的资料。",
                "citations": [],
                "debug": {
                    "retrieved_candidates": 0,
                    "returned_citations": 0,
                    "search_limit": search_limit,
                    "category_filter": category_filter,
                    "source_filter": source_filter,
                    "file_type_filter": file_type_filter,
                    "tag_filter": tag_filter,
                },
            }

        context_blocks = []
        citations = []
        for item in ranked:
            payload = item["payload"]
            context_blocks.append(f"[{payload['title']} | {payload['chunk_id']}]\n{payload['text']}")
            citations.append(
                {
                    "title": payload["title"],
                    "filename": payload.get("filename") or Path(payload["file_path"]).name,
                    "source": payload["source"],
                    "file_path": payload["file_path"],
                    "chunk_id": payload["chunk_id"],
                    "score": round(item["score"], 4),
                    "excerpt": payload["text"][:280],
                }
            )

        answer = self._generate_answer(normalized_question, context_blocks)
        return {
            "answer": answer,
            "citations": citations,
            "debug": {
                "retrieved_candidates": len(candidates),
                "returned_citations": len(citations),
                "search_limit": search_limit,
                "category_filter": category_filter,
                "source_filter": source_filter,
                "file_type_filter": file_type_filter,
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
        if not self._settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY 尚未配置，无法生成问答结果。")

        context = "\n\n".join(context_blocks) if context_blocks else "No relevant context found."
        system_prompt = (
            "You are answering only from the provided knowledge base context.\n"
            "Use the user's language.\n"
            "Be concise, practical, and explicit about uncertainty.\n"
            "If the context is insufficient, say what is missing instead of inventing facts."
        )
        user_prompt = f"Question:\n{question}\n\nContext:\n{context}"

        try:
            response = self._llm_client.responses.create(
                model=self._settings.llm_model,
                input=f"{system_prompt}\n\n{user_prompt}",
            )
            return response.output_text
        except NotFoundError:
            logger.warning("Responses API not supported by current LLM provider, falling back to chat completions.")
        except Exception as exc:
            logger.warning("Responses API failed, falling back to chat completions: %s", exc)

        chat_response = self._llm_client.chat.completions.create(
            model=self._settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        message = chat_response.choices[0].message
        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            ).strip()
        raise RuntimeError("LLM returned an unexpected response shape.")

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
