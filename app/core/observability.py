# Daily update: 2026-07-09
import os

from app.core.config import Settings


def configure_langsmith(settings: Settings) -> None:
    if not settings.langsmith_tracing:
        os.environ.setdefault("LANGSMITH_TRACING", "false")
        return

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    if settings.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
