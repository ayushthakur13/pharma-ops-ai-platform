from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from fastapi import FastAPI, Request, Response

logger = logging.getLogger("pharma_ops.observability")


def register_observability(app: FastAPI, service_name: str) -> None:
    app.state.service_name = service_name
    app.state.request_metrics = {
        "total_requests": 0,
        "responses_2xx": 0,
        "responses_4xx": 0,
        "responses_5xx": 0,
        "total_duration_ms": 0.0,
        "last_request_at": None,
    }

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next) -> Response:  # type: ignore[override]
        start = time.perf_counter()
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())

        response: Response | None = None
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            logger.exception(
                "request_failed service=%s method=%s path=%s request_id=%s",
                service_name,
                request.method,
                request.url.path,
                request_id,
            )
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            metrics: dict[str, Any] = app.state.request_metrics
            metrics["total_requests"] += 1
            metrics["total_duration_ms"] += duration_ms
            metrics["last_request_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            if 200 <= status_code < 300:
                metrics["responses_2xx"] += 1
            elif 400 <= status_code < 500:
                metrics["responses_4xx"] += 1
            elif status_code >= 500:
                metrics["responses_5xx"] += 1

            logger.info(
                "request_completed service=%s method=%s path=%s status_code=%s duration_ms=%s request_id=%s",
                service_name,
                request.method,
                request.url.path,
                status_code,
                duration_ms,
                request_id,
            )

            if response is not None:
                response.headers["x-request-id"] = request_id

    @app.get("/metrics")
    def metrics() -> dict[str, Any]:
        data: dict[str, Any] = app.state.request_metrics
        total = data["total_requests"] or 1
        avg_duration_ms = round(data["total_duration_ms"] / total, 2)
        return {
            "service": service_name,
            "total_requests": data["total_requests"],
            "responses_2xx": data["responses_2xx"],
            "responses_4xx": data["responses_4xx"],
            "responses_5xx": data["responses_5xx"],
            "avg_duration_ms": avg_duration_ms,
            "last_request_at": data["last_request_at"],
        }
