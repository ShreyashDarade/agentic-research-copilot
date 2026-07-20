# Daily update: 2026-07-20
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.observability import configure_langsmith


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    configure_langsmith(settings)
    settings.ensure_artifact_dir()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
        description="Agentic research assistant with RAG, claim verification, and approval gates.",
    )
    app.include_router(router)
    app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
    return app


app = create_app()


def main() -> None:
    settings = get_settings()
    uvicorn.run("app.main:create_app", factory=True, host=settings.api_host, port=settings.api_port)


if __name__ == "__main__":
    main()
