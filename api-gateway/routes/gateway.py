from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, status

from shared.config import settings

router = APIRouter(prefix="/api", tags=["gateway"])
logger = logging.getLogger("api_gateway")
RATE_LIMIT_LOCK = threading.Lock()
RATE_LIMIT_BUCKETS: dict[str, deque[float]] = defaultdict(deque)

UPSTREAM_BY_PREFIX = {
    "auth": settings.auth_service_url,
    "inventory": settings.inventory_service_url,
    "billing": settings.billing_service_url,
    "ai": settings.ai_service_url,
    "sync": settings.sync_service_url,
    "analytics": settings.analytics_service_url,
}

SAFE_REQUEST_HEADERS = {
    "accept",
    "authorization",
    "content-type",
    "x-request-id",
    "x-correlation-id",
    "user-agent",
}

HOP_BY_HOP_RESPONSE_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "content-encoding",
    "content-length",
}


def _resolve_upstream(path: str, query: str) -> tuple[str, str]:
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown API route")

    service_prefix = path.split("/", 1)[0]
    base = UPSTREAM_BY_PREFIX.get(service_prefix)
    if not base:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown API route")

    url = f"{base.rstrip('/')}/api/{path}"
    if query:
        url = f"{url}?{query}"
    return service_prefix, url


def _safe_forward_headers(request: Request) -> dict[str, str]:
    headers: dict[str, str] = {}
    for key, value in request.headers.items():
        lowered = key.lower()
        if lowered in SAFE_REQUEST_HEADERS:
            headers[key] = value
    return headers


def _safe_response_headers(headers: httpx.Headers) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in HOP_BY_HOP_RESPONSE_HEADERS:
            continue
        result[key] = value
    return result


async def _enforce_request_size_limit(request: Request) -> bytes:
    body = await request.body()

    if len(body) > settings.gateway_max_request_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Request body exceeds limit of {settings.gateway_max_request_size_bytes} bytes",
        )

    return body


async def _enforce_auth(auth_header: str | None) -> None:
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_or_missing_token")

    auth_url = f"{settings.auth_service_url.rstrip('/')}/api/auth/me"
    try:
        async with httpx.AsyncClient(timeout=settings.gateway_timeout_seconds) as client:
            response = await client.get(auth_url, headers={"Authorization": auth_header})
    except httpx.TimeoutException:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="auth_service_timeout")
    except httpx.RequestError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="auth_service_unavailable")

    if response.status_code in {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_or_missing_token")

    if response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="auth_service_unavailable")

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_or_missing_token")


def _rate_limit_key(request: Request) -> str:
    client_host = request.client.host if request.client else "unknown"
    auth_header = request.headers.get("authorization", "")
    token_hint = auth_header[:24]
    return f"{client_host}:{token_hint}"


async def _enforce_rate_limit(request: Request) -> None:
    if not settings.gateway_rate_limit_enabled:
        return

    now = time.monotonic()
    key = _rate_limit_key(request)
    window_seconds = settings.gateway_rate_limit_window_seconds
    max_requests = settings.gateway_rate_limit_requests

    with RATE_LIMIT_LOCK:
        bucket = RATE_LIMIT_BUCKETS[key]
        while bucket and (now - bucket[0]) > window_seconds:
            bucket.popleft()

        if len(bucket) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="rate_limit_exceeded",
            )

        bucket.append(now)


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def pass_through(path: str, request: Request) -> Response:
    await _enforce_rate_limit(request)
    body = await _enforce_request_size_limit(request)
    service_prefix, target_url = _resolve_upstream(path=path, query=request.url.query)

    if service_prefix != "auth":
        await _enforce_auth(request.headers.get("authorization"))

    headers = _safe_forward_headers(request)

    logger.info("gateway_forward method=%s path=/api/%s target=%s", request.method, path, target_url)

    try:
        async with httpx.AsyncClient(timeout=settings.gateway_timeout_seconds) as client:
            upstream_response = await client.request(
                method=request.method,
                url=target_url,
                content=body,
                headers=headers,
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="gateway_timeout")
    except httpx.RequestError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="service_unavailable")

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=_safe_response_headers(upstream_response.headers),
    )
