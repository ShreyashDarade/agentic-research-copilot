# Daily update: 2026-06-21
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root (two levels up from this file: app/core/config.py -> repo root).
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Agentic Research Assistant"
    app_env: Literal["local", "test", "staging", "production"] = "local"
    # Debug must never be force-enabled in production; see `debug` for the effective value.
    app_debug: bool = True
    api_host: str = "0.0.0.0"  # noqa: S104 - containers bind all interfaces by design
    api_port: int = 8000

    # CORS: empty means same-origin only (no cross-origin access granted).
    cors_allow_origins: list[str] = Field(default_factory=list)

    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://research:research@localhost:5432/research",
        validate_default=True,
    )
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "research_chunks"

    # Backends default to in-process implementations so the demo runs with no external infra.
    persistence_backend: Literal["memory", "postgres"] = "memory"
    vector_backend: Literal["memory", "qdrant"] = "memory"

    artifact_dir: Path = Path("storage/artifacts")
    embedding_provider: Literal["hash", "openai"] = "hash"
    embedding_dimensions: int = 384
    llm_provider: Literal["mock", "openai"] = "mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # Outbound-fetch safety limits (SSRF / resource-exhaustion protection).
    fetch_timeout_seconds: float = 15.0
    fetch_max_bytes: int = 5_000_000
    pdf_max_bytes: int = 15_000_000
    # When False, ingestion refuses URLs that resolve to private/loopback/link-local addresses.
    allow_private_network_fetch: bool = False

    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "agentic-research-assistant"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.app_env in {"staging", "production"}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def debug(self) -> bool:
        """Effective debug flag; always disabled in staging/production regardless of app_debug."""
        return self.app_debug and not self.is_production

    @property
    def artifact_path(self) -> Path:
        """Absolute artifact directory, resolved relative to the project root when not absolute."""
        path = self.artifact_dir
        return path if path.is_absolute() else PROJECT_ROOT / path

    def ensure_artifact_dir(self) -> Path:
        target = self.artifact_path
        target.mkdir(parents=True, exist_ok=True)
        return target


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
