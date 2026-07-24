from dataclasses import dataclass


@dataclass
class Chunk:
    chunk_id: str
    content: str
    start_index: int
    end_index: int


def split_text(text: str, chunk_size: int, overlap: int) -> list[Chunk]:
    normalized = " ".join(text.split())
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

