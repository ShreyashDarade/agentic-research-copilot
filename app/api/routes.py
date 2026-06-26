# Daily update: 2026-06-26
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.schemas import (
    ApprovalRequest,
    CreateResearchRunRequest,
    HealthResponse,
    ResearchRunResponse,
)
from app.core.config import Settings, get_settings
from app.services.research_service import ResearchService

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")
_service = ResearchService()
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_research_service() -> ResearchService:
    return _service


ResearchServiceDep = Annotated[ResearchService, Depends(get_research_service)]


@router.get("/api/health", response_model=HealthResponse)
async def health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(
        status="ok",
        qdrant_collection=settings.qdrant_collection,
        langsmith_tracing=settings.langsmith_tracing,
    )


@router.post(
    "/api/research-runs",
    response_model=ResearchRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_research_run(
    payload: CreateResearchRunRequest,
    service: ResearchServiceDep,
) -> ResearchRunResponse:
    return await service.create_run(payload)


@router.get("/api/research-runs", response_model=list[ResearchRunResponse])
async def list_research_runs(
    service: ResearchServiceDep,
) -> list[ResearchRunResponse]:
    return service.list_runs()


@router.get("/api/research-runs/{run_id}", response_model=ResearchRunResponse)
async def get_research_run(
    run_id: str,
    service: ResearchServiceDep,
) -> ResearchRunResponse:
    run = service.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run


@router.post("/api/research-runs/{run_id}/approval", response_model=ResearchRunResponse)
async def approve_research_run(
    run_id: str,
    payload: ApprovalRequest,
    service: ResearchServiceDep,
) -> ResearchRunResponse:
    run = await service.approve_run(
        run_id=run_id,
        approved=payload.approved,
        reviewer=payload.reviewer,
        notes=payload.notes,
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    service: ResearchServiceDep,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"runs": service.list_runs()},
    )


@router.post("/dashboard/research-runs")
async def dashboard_create_run(
    topic: Annotated[str, Form()],
    service: ResearchServiceDep,
    source_urls: Annotated[str, Form()] = "",
    constraints: Annotated[str | None, Form()] = None,
) -> RedirectResponse:
    urls = [item.strip() for item in source_urls.splitlines() if item.strip()]
    run = await service.create_run(
        CreateResearchRunRequest(topic=topic, source_urls=urls, constraints=constraints or None)
    )
    return RedirectResponse(f"/runs/{run.run_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/runs/{run_id}", response_class=HTMLResponse)
async def run_detail(
    request: Request,
    run_id: str,
    service: ResearchServiceDep,
) -> HTMLResponse:
    run = service.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Research run not found")
    return templates.TemplateResponse(request, "run_detail.html", {"run": run})


@router.post("/dashboard/research-runs/{run_id}/approval")
async def dashboard_approve_run(
    run_id: str,
    service: ResearchServiceDep,
    approved: Annotated[bool, Form()] = True,
    reviewer: Annotated[str, Form()] = "human",
    notes: Annotated[str | None, Form()] = None,
) -> RedirectResponse:
    await service.approve_run(run_id=run_id, approved=approved, reviewer=reviewer, notes=notes)
    return RedirectResponse(f"/runs/{run_id}", status_code=status.HTTP_303_SEE_OTHER)
