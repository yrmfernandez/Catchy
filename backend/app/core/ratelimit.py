"""A small in-process rate limiter.

Fixed-window, keyed by client IP + route. This bounds brute-force login attempts
and scan abuse without a Redis round-trip. It is per-process, so a multi-instance
deployment would move the counters to Redis — noted as a deliberate limitation
rather than pretending it's distributed.

Used as a FastAPI dependency: `dependencies=[Depends(auth_rate_limiter)]`.
"""

from __future__ import annotations

import time

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int, *, enabled: bool = True) -> None:
        self._limit = limit
        self._window = window_seconds
        self._enabled = enabled
        self._hits: dict[str, list[float]] = {}

    async def __call__(self, request: Request) -> None:
        if not self._enabled:
            return
        client = request.client.host if request.client else "unknown"
        key = f"{client}:{request.url.path}"
        now = time.monotonic()
        cutoff = now - self._window

        recent = [t for t in self._hits.get(key, []) if t > cutoff]
        if len(recent) >= self._limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down.",
                headers={"Retry-After": str(self._window)},
            )
        recent.append(now)
        self._hits[key] = recent


_settings = get_settings()

scan_rate_limiter = RateLimiter(
    _settings.rate_limit_requests,
    _settings.rate_limit_window_seconds,
    enabled=_settings.rate_limit_enabled,
)
auth_rate_limiter = RateLimiter(
    _settings.auth_rate_limit_requests,
    _settings.rate_limit_window_seconds,
    enabled=_settings.rate_limit_enabled,
)
