# Daily update: 2026-07-15
from pydantic import BaseModel, Field, HttpUrl


class CreateResearchRunRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    source_urls: list[HttpUrl] = Field(default_factory=list)
    constraints: str | None = Field(default=None, max_length=2_000)


class ApprovalRequest(BaseModel):
    approved: bool
    reviewer: str = "human"
    notes: str | None = None


class ResearchRunResponse(BaseModel):
    run_id: str
    topic: str
    status: str
    draft_report: str | None = None
    final_report: str | None = None
    approval_request: dict[str, object] | None = None
    claims: list[dict[str, object]] = Field(default_factory=list)
    sources: list[dict[str, object]] = Field(default_factory=list)
    deepagents_plan: dict[str, object] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    qdrant_collection: str
    langsmith_tracing: bool
