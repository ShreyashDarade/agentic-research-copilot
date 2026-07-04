# Daily update: 2026-07-04
from app.agents.state import ApprovalRequest, ResearchClaim, ResearchRunState
from app.rag.schemas import RetrievedChunk


def plan_research(state: ResearchRunState) -> dict[str, object]:
    topic = state["topic"]
    constraints = state.get("constraints")
    questions = [
        f"What is the current state of {topic}?",
        f"Which production architecture patterns matter for {topic}?",
        f"What risks, limitations, and verification criteria apply to {topic}?",
    ]
    if constraints:
        questions.append(f"How do these constraints affect the research: {constraints}")
    return {"research_questions": questions, "status": "running"}


def prepare_retrieval(state: ResearchRunState) -> dict[str, object]:
    chunks = state.get("source_chunks", [])
    if chunks:
        return {"source_chunks": chunks}
    fallback = RetrievedChunk(
        chunk_id="chunk_demo",
        source_id="source_demo",
        text=(
            f"{state['topic']} requires source-backed research, claim verification, "
            "persistent workflow state, and a human approval gate before final output."
        ),
        score=0.75,
        metadata={"title": "Synthetic local demo source", "url": ""},
    )
    return {"source_chunks": [fallback]}


def verify_claims(state: ResearchRunState) -> dict[str, object]:
    claims: list[ResearchClaim] = []
    for chunk in state.get("source_chunks", [])[:5]:
        claim_text = _claim_from_chunk(chunk)
        claims.append(
            {
                "text": claim_text,
                "status": "supported" if chunk.score >= 0.5 else "weakly_supported",
                "evidence_chunk_ids": [chunk.chunk_id],
            }
        )
    if not claims:
        claims.append(
            {
                "text": f"No external evidence was available for {state['topic']}.",
                "status": "unsupported",
                "evidence_chunk_ids": [],
            }
        )
    return {"claims": claims}


def draft_report(state: ResearchRunState) -> dict[str, object]:
    report = _render_report(state, final=False)
    return {"draft_report": report}


def approval_gate(state: ResearchRunState) -> dict[str, object]:
    if state.get("approved"):
        return {
            "approval_request": None,
            "final_report": _render_report(state, final=True),
            "status": "completed",
        }

    request: ApprovalRequest = {
        "run_id": state["run_id"],
        "message": "Review the draft, evidence, and claim verification before finalizing.",
        "risk_level": "medium",
        "required_action": "approve_or_reject",
    }
    return {
        "approval_request": request,
        "final_report": None,
        "status": "awaiting_approval",
    }


def _claim_from_chunk(chunk: RetrievedChunk) -> str:
    sentence = chunk.text.split(".")[0].strip()
    if sentence:
        return sentence[:280]
    title = chunk.metadata.get("title", chunk.source_id)
    return f"Evidence from {title} supports the research topic"


def _render_report(state: ResearchRunState, *, final: bool) -> str:
    title_prefix = "Final" if final else "Draft"
    lines = [
        f"# {title_prefix} Research Report: {state['topic']}",
        "",
        "## Executive Summary",
        (
            f"This report analyzes {state['topic']} using source-backed retrieval "
            "and claim verification."
        ),
        "",
        "## Research Questions",
    ]
    lines.extend(f"- {question}" for question in state.get("research_questions", []))
    lines.extend(["", "## Verified Claims"])
    for claim in state.get("claims", []):
        evidence = ", ".join(claim["evidence_chunk_ids"]) or "no evidence"
        lines.append(f"- **{claim['status']}**: {claim['text']} (`{evidence}`)")
    deepagents_plan = state.get("deepagents_plan")
    if deepagents_plan:
        lines.extend(["", "## DeepAgents Harness"])
        artifact_paths = deepagents_plan.get("artifact_paths", {})
        if isinstance(artifact_paths, dict):
            lines.append("- Virtual filesystem artifacts:")
            for name, path in artifact_paths.items():
                lines.append(f"  - `{name}`: `{path}`")
        subagents = deepagents_plan.get("subagents", [])
        if isinstance(subagents, list):
            lines.append("- Delegated subagents:")
            for subagent in subagents:
                if isinstance(subagent, dict):
                    lines.append(
                        f"  - `{subagent.get('role', 'unknown')}`: {subagent.get('goal', '')}"
                    )
        compressed_context = deepagents_plan.get("compressed_context")
        if isinstance(compressed_context, str):
            lines.append("- Context compression: enabled")
    lines.extend(["", "## Sources"])
    seen: set[str] = set()
    for chunk in state.get("source_chunks", []):
        title = chunk.metadata.get("title", chunk.source_id)
        url = chunk.metadata.get("url", "")
        key = f"{title}:{url}"
        if key in seen:
            continue
        seen.add(key)
        suffix = f" - {url}" if url else ""
        lines.append(f"- {title}{suffix}")
    lines.extend(
        [
            "",
            "## Human Approval",
            "Approved for final delivery."
            if final
            else "Pending human approval before final delivery.",
        ]
    )
    return "\n".join(lines)
