from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _purge_routes_modules() -> None:
    to_delete = [
        name
        for name in sys.modules
        if name in {"routes", "schemas", "services"}
        or name.startswith("routes.")
        or name.startswith("schemas.")
        or name.startswith("services.")
    ]
    for name in to_delete:
        del sys.modules[name]


def _load_app(module_name: str, app_py: Path):
    _purge_routes_modules()
    app_dir = str(app_py.parent)
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    module = _load_module(module_name, app_py)
    return module.app


@pytest.mark.parametrize(
    ("module_name", "app_path", "expected_service"),
    [
        ("auth_app", ROOT / "services/auth-service/app.py", "auth-service"),
        ("inventory_app", ROOT / "services/inventory-service/app.py", "inventory-service"),
        ("billing_app", ROOT / "services/billing-service/app.py", "billing-service"),
        ("ai_app", ROOT / "services/ai-service/app.py", "ai-service"),
        ("analytics_app", ROOT / "services/analytics-service/app.py", "analytics-service"),
        ("sync_app", ROOT / "services/sync-service/app.py", "sync-service"),
        ("gateway_app", ROOT / "api-gateway/app.py", "api-gateway"),
    ],
)
def test_health_and_metrics_endpoints(module_name: str, app_path: Path, expected_service: str) -> None:
    app = _load_app(module_name, app_path)
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["service"] == expected_service

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    body = metrics.json()
    assert body["service"] == expected_service
    assert "total_requests" in body
    assert "avg_duration_ms" in body


def test_gateway_rejects_missing_token() -> None:
    app = _load_app("gateway_app_missing_token", ROOT / "api-gateway/app.py")
    client = TestClient(app)

    res = client.get("/api/inventory/stock/1")
    assert res.status_code == 401
    assert res.json()["detail"] == "invalid_or_missing_token"


def test_gateway_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _load_app("gateway_app_rate_limit", ROOT / "api-gateway/app.py")
    gateway_module = sys.modules["routes.gateway"]

    async def _fake_enforce_auth(auth_header: str | None) -> None:
        return None

    async def _fake_request(self, method, url, content=None, headers=None):
        request = httpx.Request(method=method, url=url)
        return httpx.Response(status_code=200, json={"ok": True}, request=request)

    gateway_module.RATE_LIMIT_BUCKETS.clear()
    monkeypatch.setattr(gateway_module, "_enforce_auth", _fake_enforce_auth)
    monkeypatch.setattr(httpx.AsyncClient, "request", _fake_request)
    monkeypatch.setattr(gateway_module.settings, "gateway_rate_limit_enabled", True)
    monkeypatch.setattr(gateway_module.settings, "gateway_rate_limit_requests", 2)
    monkeypatch.setattr(gateway_module.settings, "gateway_rate_limit_window_seconds", 60)

    client = TestClient(app)
    headers = {"Authorization": "Bearer test-token"}

    ok1 = client.get("/api/inventory/stock/1", headers=headers)
    ok2 = client.get("/api/inventory/stock/1", headers=headers)
    limited = client.get("/api/inventory/stock/1", headers=headers)

    assert ok1.status_code == 200
    assert ok2.status_code == 200
    assert limited.status_code == 429
    assert limited.json()["detail"] == "rate_limit_exceeded"
