# Daily update: 2026-07-18
from app.rag.chunking import chunk_text
from app.rag.embeddings import HashEmbeddingModel


def test_chunk_text_preserves_source_metadata_and_offsets() -> None:
    chunks = chunk_text(
        text="alpha beta gamma delta epsilon zeta eta theta",
        source_id="src_1",
        metadata={"title": "Example"},
        chunk_size=22,
        overlap=6,
    )

    assert len(chunks) >= 2
    assert chunks[0].source_id == "src_1"
    assert chunks[0].metadata["title"] == "Example"
    assert chunks[0].start_index == 0
    assert chunks[1].start_index < chunks[0].end_index


def test_hash_embedding_model_is_deterministic_and_normalized() -> None:
    model = HashEmbeddingModel(dimensions=16)

    first = model.embed_query("agentic research")
    second = model.embed_query("agentic research")

    assert first == second
    assert len(first) == 16
    assert round(sum(value * value for value in first), 6) == 1.0
