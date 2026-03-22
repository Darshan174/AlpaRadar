"""API middleware — rate limiting, auth, request logging."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings
from src.logging_config import get_logger

log = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter (per-IP, per-minute)."""

    def __init__(self, app: Callable, limit: int | None = None):
        super().__init__(app)
        self.limit = limit or settings.rate_limit_per_minute
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if now - t < 60
        ]

        if len(self._requests[client_ip]) >= self.limit:
            log.warning("rate_limited", ip=client_ip)
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        self._requests[client_ip].append(now)
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 1)

        log.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration,
        )
        return response


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Optional API key auth for protected routes."""

    PROTECTED_PREFIXES = ("/v1/analyze", "/v1/watchlist", "/v1/chat")
    PUBLIC_PATHS = ("/health", "/docs", "/openapi.json", "/v1/signals")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Skip auth for public paths
        if any(path.startswith(p) for p in self.PUBLIC_PATHS):
            return await call_next(request)

        # Check if route needs auth
        needs_auth = any(path.startswith(p) for p in self.PROTECTED_PREFIXES)
        if not needs_auth:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key", "")
        if api_key != settings.api_secret_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

        return await call_next(request)
