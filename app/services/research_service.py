# Daily update: 2026-07-11
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from app.agents.deepagents_adapter import DeepAgentResearchPlan, DeepAgentsResearchHarness
from app.agents.state import ResearchRunState
from app.agents.workflow import build_research_graph
from app.api.schemas import CreateResearchRunRequest, ResearchRunResponse
from app.rag.embeddings import HashEmbeddingModel
from app.rag.ingestion import IngestionService
from app.rag.schemas import DocumentChunk, RetrievedChunk
from app.rag.vector_store import InMemoryVectorStore


@dataclass
class StoredResearchRun:
    run_id: str
    topic: str
    constraints: str | None
    status: str
    source_chunks: list[RetrievedChunk] = field(default_factory=list)
    draft_report: str | None = None
    final_report: str | None = None
    approval_request: dict[str, object] | None = None
    claims: list[dict[str, object]] = field(default_factory=list)
    deepagents_plan: dict[str, object] = field(default_factory=dict)


class ResearchService:
    def __init__(self) -> None:
        embedding_model = HashEmbeddingModel()
        self.vector_store = InMemoryVectorStore(embedding_model)
        self.ingestion = IngestionService(self.vector_store)
        self.graph = build_research_graph()
        self.deepagents = DeepAgentsResearchHarness(artifact_dir=Path("storage/artifacts"))
        self.runs: dict[str, StoredResearchRun] = {}

    async def create_run(self, payload: CreateResearchRunRequest) -> ResearchRunResponse:
        run_id = f"run_{uuid4().hex}"
        urls = [str(url) for url in payload.source_urls]
        chunks = await self.ingestion.ingest_urls(
            run_id=run_id,
            topic=payload.topic,
            urls=urls,
        )
        retrieved = _chunks_to_retrieved(chunks)
        if not retrieved:
            retrieved = await self.vector_store.search(payload.topic, run_id=run_id)
        deepagents_plan = self.deepagents.prepare_research_context(
            run_id=run_id,
            topic=payload.topic,
            constraints=payload.constraints,
            source_chunks=retrieved,
        )
        deepagents_payload = _deepagents_plan_payload(deepagents_plan)

        result = await self.graph.ainvoke(
            ResearchRunState(
                run_id=run_id,
                topic=payload.topic,
                constraints=payload.constraints,
                source_chunks=retrieved,
                deepagents_plan=deepagents_payload,
                approved=False,
            )
        )
        stored = StoredResearchRun(
            run_id=run_id,
            topic=payload.topic,
            constraints=payload.constraints,
            status=str(result["status"]),
            source_chunks=retrieved,
            draft_report=result.get("draft_report"),
            final_report=result.get("final_report"),
            approval_request=result.get("approval_request"),
            claims=list(result.get("claims", [])),
            deepagents_plan=deepagents_payload,
        )
        self.runs[run_id] = stored
        return self._to_response(stored)

    async def approve_run(
        self,
        *,
        run_id: str,
        approved: bool,
        reviewer: str,
        notes: str | None = None,
    ) -> ResearchRunResponse | None:
        stored = self.runs.get(run_id)
        if stored is None:
            return None
        if not approved:
            stored.status = "rejected"
            stored.approval_request = None
            stored.claims.append(
                {
                    "text": notes or "Rejected by reviewer.",
                    "status": "unsupported",
                    "evidence_chunk_ids": [],
                }
            )
            return self._to_response(stored)

        result = await self.graph.ainvoke(
            ResearchRunState(
                run_id=run_id,
                topic=stored.topic,
                constraints=stored.constraints,
                approved=True,
                source_chunks=stored.source_chunks,
                claims=stored.claims,  # type: ignore[typeddict-item]
                deepagents_plan=stored.deepagents_plan,
                draft_report=stored.draft_report,
            )
        )
        stored.status = str(result["status"])
        stored.final_report = result.get("final_report")
        stored.approval_request = result.get("approval_request")
        stored.claims = list(result.get("claims", stored.claims))
        return self._to_response(stored)

    def get_run(self, run_id: str) -> ResearchRunResponse | None:
        stored = self.runs.get(run_id)
        if stored is None:
            return None
        return self._to_response(stored)

    def list_runs(self) -> list[ResearchRunResponse]:
        return [self._to_response(run) for run in reversed(list(self.runs.values()))]

    def _to_response(self, run: StoredResearchRun) -> ResearchRunResponse:
        return ResearchRunResponse(
            run_id=run.run_id,
            topic=run.topic,
            status=run.status,
            draft_report=run.draft_report,
            final_report=run.final_report,
            approval_request=run.approval_request,
            claims=run.claims,
            deepagents_plan=run.deepagents_plan,
            sources=[
                {
                    "source_id": chunk.source_id,
                    "chunk_id": chunk.chunk_id,
                    "title": chunk.metadata.get("title", chunk.source_id),
                    "url": chunk.metadata.get("url", ""),
                    "score": chunk.score,
                }
                for chunk in run.source_chunks
            ],
        )


def _chunks_to_retrieved(chunks: list[DocumentChunk]) -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk_id=chunk.chunk_id,
            source_id=chunk.source_id,
            text=chunk.text,
            score=0.9,
            metadata=chunk.metadata,
        )
        for chunk in chunks
    ]


def _deepagents_plan_payload(plan: DeepAgentResearchPlan) -> dict[str, object]:
    return {
        "capabilities": plan.capabilities.model_dump(),
        "todos": plan.todos,
        "subagents": [task.model_dump() for task in plan.subagent_tasks],
        "compressed_context": plan.compressed_context,
        "approval_policy": plan.approval_policy,
        "artifact_paths": {
            "plan": str(plan.artifacts.plan_path),
            "evidence": str(plan.artifacts.evidence_path),
            "context": str(plan.artifacts.context_path),
            "report": str(plan.artifacts.report_path),
        },
        "agent_config": plan.agent_config,
    }
