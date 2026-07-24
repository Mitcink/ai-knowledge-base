from fastapi import APIRouter

from app.models.schemas import QueryRequest, QueryResponse
from app.services.rag_service import get_rag_service


router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def answer_query(request: QueryRequest) -> QueryResponse:
    service = get_rag_service()
    result = service.answer_question(
        question=request.question,
        top_k=request.top_k,
        tag_filter=request.tag_filter,
    )
    return QueryResponse(**result)

