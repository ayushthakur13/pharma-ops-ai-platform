import sys
from pathlib import Path

from fastapi import FastAPI

# Allow standalone service execution while importing shared modules from repo root.
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from routes.analytics import router as analytics_router


def create_app() -> FastAPI:
    app = FastAPI(title="Analytics Service", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "analytics-service"}

    app.include_router(analytics_router)
    return app


app = create_app()
