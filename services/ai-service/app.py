import sys
from pathlib import Path

from fastapi import FastAPI

# Allow standalone service execution while importing shared modules from repo root.
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from routes.ai import router as ai_router
from shared.observability import register_observability


def create_app() -> FastAPI:
    app = FastAPI(title="AI Service", version="0.1.0")
    register_observability(app, service_name="ai-service")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "ai-service"}

    app.include_router(ai_router)
    return app


app = create_app()
