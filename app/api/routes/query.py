import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import QueryRequest, QueryResponse
from app.services.rag_service import get_rag_service


router = APIRouter(prefix="/query", tags=["query"])
logger = logging.getLogger(__name__)


@router.post("", response_model=QueryResponse)
def answer_query(request: QueryRequest) -> QueryResponse:
    service = get_rag_service()
    logger.info(
        "Received query request: question_length=%s, top_k=%s, category_filter=%s, source_filter=%s, file_type_filter=%s, tag_filter=%s",
        len(request.question or ""),
        request.top_k,
        request.category_filter,
        request.source_filter,
        request.file_type_filter,
        request.tag_filter,
    )
    try:
        result = service.answer_question(
            question=request.question,
            top_k=request.top_k,
            category_filter=request.category_filter,
            source_filter=request.source_filter,
            file_type_filter=request.file_type_filter,
            tag_filter=request.tag_filter,
        )
        return QueryResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Query failed")
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}") from exc
