from fastapi import APIRouter, HTTPException

from app.models.schemas import QueryRequest, QueryResponse
from app.services.rag_service import get_rag_service


router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def answer_query(request: QueryRequest) -> QueryResponse:
    service = get_rag_service()
    try:
        result = service.answer_question(
            question=request.question,
            top_k=request.top_k,
            category_filter=request.category_filter,
            tag_filter=request.tag_filter,
        )
        return QueryResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}") from exc
