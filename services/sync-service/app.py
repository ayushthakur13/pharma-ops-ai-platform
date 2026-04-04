import sys
from pathlib import Path

from fastapi import FastAPI

# Allow standalone service execution while importing shared modules from repo root.
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from routes.sync import router as sync_router


def create_app() -> FastAPI:
    app = FastAPI(title="Sync Service", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "sync-service"}

    app.include_router(sync_router)
    return app


app = create_app()
