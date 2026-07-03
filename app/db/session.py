# Daily update: 2026-07-03
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings


def create_engine(settings: Settings | None = None) -> AsyncEngine:
    resolved = settings or get_settings()
    return create_async_engine(
        resolved.database_url.unicode_string(),
        pool_pre_ping=True,
        future=True,
    )


def create_session_factory(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(create_engine(settings), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    factory = create_session_factory()
    async with factory() as session:
        yield session
