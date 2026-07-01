# Daily update: 2026-07-01
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypedDict

from pydantic import BaseModel, Field

from app.rag.schemas import RetrievedChunk


class DeepAgentCapabilityProfile(BaseModel):
    planning: bool = True
    virtual_filesystem: bool = True
    subagents: bool = True
    context_compression: bool = True
    human_approval: bool = True
    long_term_memory: bool = True
    mcp_ready_tools: bool = True


class DeepAgentArtifactManifest(BaseModel):
    run_dir: Path
    plan_path: Path
    evidence_path: Path
    context_path: Path
    report_path: Path


class DeepAgentSubagentTask(BaseModel):
    role: str
    goal: str
    handoff_contract: str


class DeepAgentResearchPlan(BaseModel):
    run_id: str
    topic: str
    capabilities: DeepAgentCapabilityProfile
    artifacts: DeepAgentArtifactManifest
    todos: list[str] = Field(default_factory=list)
    subagent_tasks: list[DeepAgentSubagentTask] = Field(default_factory=list)
    compressed_context: str
    approval_policy: dict[str, object]
    system_prompt: str
    agent_config: dict[str, object]


class DeepAgentRuntimeConfiguration(TypedDict):
    model: str
    tools: list[str]
    system_prompt: str
    interrupt_on: dict[str, bool]
    permissions: list[dict[str, object]]
    subagents: list[dict[str, object]]


class DeepAgentsResearchHarness:
    """DeepAgents integration boundary for long-running research work.

    DeepAgents provides the high-level agent harness: planning, filesystem-backed
    artifacts, subagent delegation, context compression, and human approval. This
    class makes those capabilities explicit and keeps a deterministic local path
    for tests and no-key demos.
    """

    def __init__(
        self,
        *,
        artifact_dir: Path,
        model: str = "openai:gpt-5.5",
        create_agent: Callable[..., Any] | None = None,
    ) -> None:
        self.artifact_dir = artifact_dir
        self.model = model
        self._create_agent = create_agent

    def prepare_research_context(
        self,
        *,
        run_id: str,
        topic: str,
        constraints: str | None,
        source_chunks: list[RetrievedChunk],
    ) -> DeepAgentResearchPlan:
        run_dir = self.artifact_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        artifacts = DeepAgentArtifactManifest(
            run_dir=run_dir,
            plan_path=run_dir / "plan.md",
            evidence_path=run_dir / "evidence.md",
            context_path=run_dir / "compressed_context.md",
            report_path=run_dir / "final_report.md",
        )
        todos = self._build_todos(topic=topic, constraints=constraints)
        subagent_tasks = self._build_subagent_tasks(topic)
        compressed_context = self._compress_context(topic=topic, chunks=source_chunks)
        system_prompt = self._system_prompt()
        agent_config = self.agent_configuration()

        artifacts.plan_path.write_text(_render_plan(todos), encoding="utf-8")
        artifacts.evidence_path.write_text(
            _render_evidence(source_chunks),
            encoding="utf-8",
        )
        artifacts.context_path.write_text(compressed_context, encoding="utf-8")

        return DeepAgentResearchPlan(
            run_id=run_id,
            topic=topic,
            capabilities=DeepAgentCapabilityProfile(),
            artifacts=artifacts,
            todos=todos,
            subagent_tasks=subagent_tasks,
            compressed_context=compressed_context,
            approval_policy=self._approval_policy(),
            system_prompt=system_prompt,
            agent_config=dict(agent_config),
        )

    def agent_configuration(self) -> DeepAgentRuntimeConfiguration:
        return {
            "model": self.model,
            "tools": [
                "retrieve_evidence",
                "write_research_plan",
                "write_evidence_file",
                "write_final_report",
            ],
            "system_prompt": self._system_prompt(),
            "interrupt_on": {"write_final_report": True},
            "permissions": [
                {
                    "path": "storage/artifacts/**",
                    "operations": ["read", "write"],
                    "mode": "allow",
                },
                {
                    "path": ".env*",
                    "operations": ["read", "write"],
                    "mode": "deny",
                },
            ],
            "subagents": [
                task.model_dump() for task in self._build_subagent_tasks("research topic")
            ],
        }

    def create_runtime_agent(self) -> Any:
        create_agent = self._create_agent or _load_create_deep_agent()
        config = self.agent_configuration()
        return create_agent(
            model=config["model"],
            tools=[
                retrieve_evidence,
                write_research_plan,
                write_evidence_file,
                write_final_report,
            ],
            system_prompt=config["system_prompt"],
            interrupt_on=config["interrupt_on"],
        )

    def _build_todos(self, *, topic: str, constraints: str | None) -> list[str]:
        todos = [
            f"Define research scope for: {topic}",
            "Collect and normalize source evidence.",
            "Delegate source analysis to source_analyst subagent.",
            "Delegate claim verification to claim_verifier subagent.",
            "Draft cited report with explicit limitations.",
            "Pause for human approval before final report write.",
        ]
        if constraints:
            todos.insert(1, f"Apply user constraints: {constraints}")
        return todos

    def _build_subagent_tasks(self, topic: str) -> list[DeepAgentSubagentTask]:
        return [
            DeepAgentSubagentTask(
                role="source_analyst",
                goal=f"Extract source-backed insights for {topic}.",
                handoff_contract="Return concise source notes with chunk IDs and URLs.",
            ),
            DeepAgentSubagentTask(
                role="claim_verifier",
                goal="Check every draft claim against retrieved evidence.",
                handoff_contract="Return support label, evidence chunk IDs, and uncertainty notes.",
            ),
            DeepAgentSubagentTask(
                role="report_writer",
                goal="Write the final report only after approval.",
                handoff_contract="Return Markdown with citations and limitations.",
            ),
        ]

    def _compress_context(self, *, topic: str, chunks: list[RetrievedChunk]) -> str:
        evidence_lines = []
        for chunk in chunks[:8]:
            title = chunk.metadata.get("title", chunk.source_id)
            evidence_lines.append(f"- `{chunk.chunk_id}` from {title}: {chunk.text[:300].strip()}")
        evidence = "\n".join(evidence_lines) or "- No external chunks available."
        return (
            "# compressed_context\n\n"
            f"Topic: {topic}\n\n"
            "Important evidence retained for the DeepAgents harness:\n"
            f"{evidence}\n\n"
            "Context policy: preserve provenance, drop duplicate wording, keep chunk IDs."
        )

    def _approval_policy(self) -> dict[str, object]:
        return {
            "interrupt_on": ["write_final_report"],
            "requires_human_review": True,
            "risk_level": "medium",
            "reason": "Final reports can influence user decisions and must be source-reviewed.",
        }

    def _system_prompt(self) -> str:
        return (
            "You are EvidenceGraph AI, a source-grounded research deep agent. "
            "Plan work with todos, use evidence retrieval tools, delegate isolated work "
            "to specialized subagents, write artifacts to the virtual filesystem, compress "
            "long context, and stop for human approval before write_final_report."
        )


def describe_deepagents_fit() -> DeepAgentCapabilityProfile:
    return DeepAgentCapabilityProfile()


def retrieve_evidence(query: str) -> str:
    return f"Retrieve evidence for query: {query}"


def write_research_plan(plan_markdown: str) -> str:
    return f"Research plan prepared with {len(plan_markdown)} characters."


def write_evidence_file(evidence_markdown: str) -> str:
    return f"Evidence file prepared with {len(evidence_markdown)} characters."


def write_final_report(report_markdown: str) -> str:
    return f"Final report prepared with {len(report_markdown)} characters."


def _load_create_deep_agent() -> Callable[..., Any]:
    try:
        from deepagents import create_deep_agent
    except ImportError as exc:
        raise RuntimeError(
            "Install the `deepagents` package and configure a model provider to create "
            "a live DeepAgents runtime agent."
        ) from exc
    return create_deep_agent


def _render_plan(todos: list[str]) -> str:
    lines = ["# DeepAgents Research Plan", ""]
    lines.extend(f"- [ ] {todo}" for todo in todos)
    return "\n".join(lines)


def _render_evidence(chunks: list[RetrievedChunk]) -> str:
    lines = ["# Evidence", ""]
    for chunk in chunks:
        title = chunk.metadata.get("title", chunk.source_id)
        url = chunk.metadata.get("url", "")
        lines.extend(
            [
                f"## {chunk.chunk_id}",
                f"- Source: {title}",
                f"- URL: {url}",
                f"- Score: {chunk.score:.2f}",
                "",
                chunk.text,
                "",
            ]
        )
    if len(lines) == 2:
        lines.append("No evidence chunks were available.")
    return "\n".join(lines)
