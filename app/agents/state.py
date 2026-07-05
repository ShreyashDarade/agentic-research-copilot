# Daily update: 2026-07-05
from typing import TypedDict

from app.rag.schemas import RetrievedChunk


class ResearchClaim(TypedDict):
    text: str
    status: str
    evidence_chunk_ids: list[str]


class ApprovalRequest(TypedDict):
    run_id: str
    message: str
    risk_level: str
    required_action: str


class ResearchRunState(TypedDict, total=False):
    run_id: str
    topic: str
    constraints: str | None
    approved: bool
    status: str
    research_questions: list[str]
    source_chunks: list[RetrievedChunk]
    claims: list[ResearchClaim]
    deepagents_plan: dict[str, object]
    draft_report: str | None
    final_report: str | None
    approval_request: ApprovalRequest | None
