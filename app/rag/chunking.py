# Daily update: 2026-07-24
from collections.abc import Iterator
from hashlib import sha256

from app.rag.schemas import DocumentChunk


def _window_starts(text_length: int, chunk_size: int, overlap: int) -> Iterator[int]:
    step = max(1, chunk_size - overlap)
    current = 0
    while current < text_length:
        yield current
        current += step


def chunk_text(
    *,
    text: str,
    source_id: str,
    metadata: dict[str, str] | None = None,
    chunk_size: int = 1_200,
    overlap: int = 160,
) -> list[DocumentChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks: list[DocumentChunk] = []
    base_metadata = metadata or {}
    for start in _window_starts(len(normalized), chunk_size, overlap):
        end = min(len(normalized), start + chunk_size)
        chunk_body = normalized[start:end].strip()
        if not chunk_body:
            continue
        digest = sha256(f"{source_id}:{start}:{chunk_body}".encode()).hexdigest()[:16]
        chunks.append(
            DocumentChunk(
                chunk_id=f"chk_{digest}",
                source_id=source_id,
                text=chunk_body,
                start_index=start,
                end_index=end,
                metadata=dict(base_metadata),
            )
        )
        if end == len(normalized):
            break
    return chunks
