# Daily update: 2026-07-19
from pathlib import Path

from app.agents.deepagents_adapter import DeepAgentsResearchHarness
from app.rag.schemas import RetrievedChunk


def test_deepagents_harness_builds_research_plan_with_artifacts_and_subagents(
    tmp_path: Path,
) -> None:
    harness = DeepAgentsResearchHarness(artifact_dir=tmp_path)
    chunks = [
        RetrievedChunk(
            chunk_id="chunk_1",
            source_id="source_1",
            text="Agentic research systems need planning, retrieval, verification, and approval.",
            score=0.92,
            metadata={"title": "Agent Systems", "url": "https://example.com/agents"},
        )
    ]

    plan = harness.prepare_research_context(
        run_id="run_1",
        topic="Agentic AI research assistants",
        constraints="Focus on production readiness.",
        source_chunks=chunks,
    )

    assert plan.capabilities.planning is True
    assert plan.capabilities.virtual_filesystem is True
    assert plan.capabilities.subagents is True
    assert plan.capabilities.context_compression is True
    assert plan.capabilities.human_approval is True
    assert plan.artifacts.evidence_path.name == "evidence.md"
    assert plan.artifacts.plan_path.exists()
    assert plan.artifacts.evidence_path.exists()
    assert {task.role for task in plan.subagent_tasks} == {
        "source_analyst",
        "claim_verifier",
        "report_writer",
    }
    assert "compressed_context" in plan.model_dump()


def test_deepagents_harness_configures_real_agent_when_package_is_available(
    tmp_path: Path,
) -> None:
    harness = DeepAgentsResearchHarness(artifact_dir=tmp_path)
    config = harness.agent_configuration()

    assert config["model"].startswith("openai:")
    assert "retrieve_evidence" in config["tools"]
    assert config["interrupt_on"]["write_final_report"] is True
    assert "source-grounded research" in config["system_prompt"]
