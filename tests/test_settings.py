# Daily update: 2026-07-11
from app.core.config import Settings


def test_settings_build_database_url_from_environment() -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://research:research@localhost:5432/research",
        qdrant_url="http://localhost:6333",
        artifact_dir="storage/artifacts",
    )

    assert settings.database_url.unicode_string().startswith("postgresql+asyncpg://")
    assert settings.qdrant_url == "http://localhost:6333"
    assert settings.artifact_dir.name == "artifacts"


def test_settings_enable_local_demo_mode_by_default() -> None:
    settings = Settings()

    assert settings.llm_provider == "mock"
    assert settings.embedding_provider == "hash"
