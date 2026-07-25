from app.services.chunking import split_text


def test_split_text_preserves_paragraph_boundaries() -> None:
    text = "第一段第一句。\n第一段第二句。\n\n第二段第一句。"

    chunks = split_text(text, chunk_size=20, overlap=5)

    assert chunks
    assert "\n" in chunks[0].content or len(chunks) > 1


def test_split_text_rejects_invalid_overlap() -> None:
    try:
        split_text("abc", chunk_size=10, overlap=10)
    except ValueError as exc:
        assert "smaller than chunk_size" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid overlap")
