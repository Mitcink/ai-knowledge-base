from dataclasses import dataclass


@dataclass
class Chunk:
    chunk_id: str
    content: str
    start_index: int
    end_index: int


def split_text(text: str, chunk_size: int, overlap: int) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap < 0:
        raise ValueError("overlap must be 0 or greater")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    normalized = _normalize_text(text)
    if not normalized:
        return []

    chunks: list[Chunk] = []
    start = 0
    index = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        content = normalized[start:end].strip()
        if content:
            chunks.append(
                Chunk(
                    chunk_id=f"chunk-{index}",
                    content=content,
                    start_index=start,
                    end_index=end,
                )
            )
            index += 1
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks


def _normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    paragraphs = [" ".join(line.split()) for line in lines if line.strip()]
    return "\n".join(paragraphs).strip()

