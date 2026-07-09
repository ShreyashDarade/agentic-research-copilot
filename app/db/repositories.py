# Daily update: 2026-07-09
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Approval, Claim, Report, ResearchRun, ResearchRunStatus, Source


class ResearchRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, topic: str, constraints: str | None) -> ResearchRun:
        run = ResearchRun(topic=topic, constraints=constraints, status=ResearchRunStatus.queued)
        self.session.add(run)
        await self.session.flush()
        return run

    async def get(self, run_id: str) -> ResearchRun | None:
        return await self.session.get(ResearchRun, run_id)

    async def list_recent(self, *, limit: int = 25) -> Sequence[ResearchRun]:
        result = await self.session.execute(
            select(ResearchRun).order_by(ResearchRun.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

    async def add_source(self, source: Source) -> Source:
        self.session.add(source)
        await self.session.flush()
        return source

    async def add_claim(self, claim: Claim) -> Claim:
        self.session.add(claim)
        await self.session.flush()
        return claim

    async def add_approval(self, approval: Approval) -> Approval:
        self.session.add(approval)
        await self.session.flush()
        return approval

    async def add_report(self, report: Report) -> Report:
        self.session.add(report)
        await self.session.flush()
        return report
