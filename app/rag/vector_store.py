# Daily update: 2026-06-27
from collections.abc import Sequence
from typing import Protocol

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
)
from qdrant_client.models import VectorParams

from app.rag.embeddings import EmbeddingModel
from app.rag.schemas import DocumentChunk, RetrievedChunk


class VectorStore(Protocol):
    async def upsert_chunks(self, chunks: Sequence[DocumentChunk]) -> None:
        raise NotImplementedError

    async def search(
        self, query: str, *, limit: int = 8, run_id: str | None = None
    ) -> list[RetrievedChunk]:
        raise NotImplementedError


class InMemoryVectorStore:
    def __init__(self, embedding_model: EmbeddingModel) -> None:
        self.embedding_model = embedding_model
        self._items: list[tuple[DocumentChunk, list[float]]] = []

    async def upsert_chunks(self, chunks: Sequence[DocumentChunk]) -> None:
        vectors = self.embedding_model.embed_documents([chunk.text for chunk in chunks])
        self._items.extend(zip(chunks, vectors, strict=True))

    async def search(
        self, query: str, *, limit: int = 8, run_id: str | None = None
    ) -> list[RetrievedChunk]:
        query_vector = self.embedding_model.embed_query(query)
        scored: list[RetrievedChunk] = []
        for chunk, vector in self._items:
            if run_id and chunk.metadata.get("run_id") != run_id:
                continue
            score = sum(left * right for left, right in zip(query_vector, vector, strict=True))
            scored.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    source_id=chunk.source_id,
                    text=chunk.text,
                    score=score,
                    metadata=chunk.metadata,
                )
            )
        return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]


class QdrantVectorStore:
    def __init__(
        self,
        *,
        client: AsyncQdrantClient,
        collection_name: str,
        embedding_model: EmbeddingModel,
    ) -> None:
        self.client = client
        self.collection_name = collection_name
        self.embedding_model = embedding_model

    async def ensure_collection(self) -> None:
        collections = await self.client.get_collections()
        existing = {collection.name for collection in collections.collections}
        if self.collection_name in existing:
            return
        await self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.embedding_model.dimensions,
                distance=Distance.COSINE,
            ),
        )

    async def upsert_chunks(self, chunks: Sequence[DocumentChunk]) -> None:
        await self.ensure_collection()
        vectors = self.embedding_model.embed_documents([chunk.text for chunk in chunks])
        points = [
            PointStruct(
                id=chunk.chunk_id,
                vector=vector,
                payload={
                    "source_id": chunk.source_id,
                    "text": chunk.text,
                    **chunk.metadata,
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        if points:
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

    async def search(
        self, query: str, *, limit: int = 8, run_id: str | None = None
    ) -> list[RetrievedChunk]:
        await self.ensure_collection()
        query_filter = None
        if run_id:
            query_filter = Filter(
                must=[FieldCondition(key="run_id", match=MatchValue(value=run_id))]
            )
        results = await self.client.query_points(
            collection_name=self.collection_name,
            query=self.embedding_model.embed_query(query),
            query_filter=query_filter,
            limit=limit,
        )
        return [
            RetrievedChunk(
                chunk_id=str(point.id),
                source_id=str((point.payload or {}).get("source_id", "")),
                text=str((point.payload or {}).get("text", "")),
                score=float(point.score),
                metadata={
                    key: str(value) for key, value in (point.payload or {}).items() if key != "text"
                },
            )
            for point in results.points
        ]
