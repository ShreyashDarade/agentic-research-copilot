# Daily update: 2026-07-10
import pytest

from app.agents.state import ResearchRunState
from app.agents.workflow import build_research_graph
from app.rag.schemas import RetrievedChunk


@pytest.mark.asyncio
async def test_workflow_pauses_for_human_approval_before_final_report() -> None:
    graph = build_research_graph()
    state = ResearchRunState(
        run_id="run_1",
        topic="AI agents in software engineering",
        source_chunks=[
            RetrievedChunk(
                chunk_id="chunk_1",
                source_id="source_1",
                text="AI agents can use tools and verify software changes with tests.",
                score=0.95,
                metadata={"title": "Agent Report", "url": "https://example.com/agents"},
            )
        ],
    )

    result = await graph.ainvoke(state)

    assert result["status"] == "awaiting_approval"
    assert result["draft_report"]
    assert result["approval_request"]["risk_level"] == "medium"
    assert result["final_report"] is None


@pytest.mark.asyncio
async def test_workflow_writes_final_report_after_approval() -> None:
    graph = build_research_graph()
    state = ResearchRunState(
        run_id="run_2",
        topic="AI agents in software engineering",
        approved=True,
        source_chunks=[
            RetrievedChunk(
                chunk_id="chunk_1",
                source_id="source_1",
                text="AI agents can use tools and verify software changes with tests.",
                score=0.95,
                metadata={"title": "Agent Report", "url": "https://example.com/agents"},
            )
        ],
    )

    result = await graph.ainvoke(state)

    assert result["status"] == "completed"
    assert "## Sources" in result["final_report"]
    assert result["approval_request"] is None
