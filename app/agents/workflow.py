# Daily update: 2026-06-21
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    approval_gate,
    draft_report,
    plan_research,
    prepare_retrieval,
    verify_claims,
)
from app.agents.state import ResearchRunState


def build_research_graph() -> Any:
    graph = StateGraph(ResearchRunState)
    graph.add_node("planner", plan_research)
    graph.add_node("retrieval", prepare_retrieval)
    graph.add_node("verifier", verify_claims)
    graph.add_node("writer", draft_report)
    graph.add_node("approval", approval_gate)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "retrieval")
    graph.add_edge("retrieval", "verifier")
    graph.add_edge("verifier", "writer")
    graph.add_edge("writer", "approval")
    graph.add_edge("approval", END)
    return graph.compile()
