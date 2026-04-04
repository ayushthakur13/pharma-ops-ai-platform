import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Allow standalone gateway execution while importing shared modules from repo root.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from routes.gateway import router as gateway_router
from shared.config import settings
from shared.observability import register_observability


def create_app() -> FastAPI:
    app = FastAPI(title="API Gateway", version="0.1.0")
    register_observability(app, service_name="api-gateway")

    origins = [origin.strip() for origin in settings.gateway_cors_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "api-gateway"}

    app.include_router(gateway_router)
    return app


app = create_app()
