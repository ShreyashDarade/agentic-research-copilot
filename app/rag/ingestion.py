from collections.abc import Sequence

from app.rag.chunking import chunk_text
from app.rag.loaders import load_pdf_bytes, load_url, synthetic_document
from app.rag.schemas import DocumentChunk, SourceDocument
from app.rag.vector_store import VectorStore


class IngestionService:
    def __init__(self, vector_store: VectorStore) -> None:
        self.vector_store = vector_store

    async def ingest_documents(
        self,
        *,
        run_id: str,
        documents: Sequence[SourceDocument],
    ) -> list[DocumentChunk]:
        all_chunks: list[DocumentChunk] = []
        for document in documents:
            chunks = chunk_text(
                text=document.text,
                source_id=document.source_id,
                metadata={
                    **document.metadata,
                    "run_id": run_id,
                    "title": document.title,
                    "source_type": document.source_type,
                },
            )
            all_chunks.extend(chunks)
        await self.vector_store.upsert_chunks(all_chunks)
        return all_chunks

    async def ingest_urls(
        self,
        *,
        run_id: str,
        topic: str,
        urls: Sequence[str],
        allow_synthetic_fallback: bool = True,
    ) -> list[DocumentChunk]:
        documents: list[SourceDocument] = []
        for url in urls:
            try:
                documents.append(await load_url(url))
            except Exception:
                if not allow_synthetic_fallback:
                    raise
                documents.append(synthetic_document(topic=topic, url=url))
        if not documents:
            documents.append(synthetic_document(topic=topic))
        return await self.ingest_documents(run_id=run_id, documents=documents)

    async def ingest_pdf(
        self,
        *,
        run_id: str,
        filename: str,
        content: bytes,
    ) -> list[DocumentChunk]:
        document = load_pdf_bytes(filename=filename, content=content)
        return await self.ingest_documents(run_id=run_id, documents=[document])
