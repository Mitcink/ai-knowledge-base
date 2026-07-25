import pytest

from app.models.schemas import QueryRequest


def test_query_request_rejects_blank_question() -> None:
    with pytest.raises(ValueError):
        QueryRequest(question="   ")


def test_query_request_limits_top_k() -> None:
    request = QueryRequest(question="什么是 RAG？", top_k=6)
    assert request.top_k == 6
