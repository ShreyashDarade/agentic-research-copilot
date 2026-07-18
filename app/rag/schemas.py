# Daily update: 2026-07-18
from pydantic import BaseModel, Field, HttpUrl


class SourceDocument(BaseModel):
    source_id: str
    title: str
    text: str
    source_type: str
    url: HttpUrl | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    chunk_id: str
    source_id: str
    text: str
    start_index: int
    end_index: int
    metadata: dict[str, str] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    chunk_id: str
    source_id: str
    text: str
    score: float
    metadata: dict[str, str] = Field(default_factory=dict)
