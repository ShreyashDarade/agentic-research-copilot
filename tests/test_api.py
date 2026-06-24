# Daily update: 2026-06-24
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.asyncio
async def test_health_endpoint_reports_dependencies() -> None:
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "qdrant_collection" in response.json()


@pytest.mark.asyncio
async def test_create_research_run_returns_awaiting_approval() -> None:
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/research-runs",
            json={
                "topic": "AI agents for production engineering",
                "source_urls": ["https://example.com/agents"],
                "constraints": "Include verification and governance.",
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["topic"] == "AI agents for production engineering"
    assert payload["status"] == "awaiting_approval"
    assert payload["draft_report"]
    assert payload["deepagents_plan"]["capabilities"]["subagents"] is True
    assert "DeepAgents Harness" in payload["draft_report"]
