"""Security hardening: rate limiting and response headers."""

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.ratelimit import RateLimiter
from app.main import app

client = TestClient(app)


def _fake_request(ip: str = "1.2.3.4", path: str = "/x") -> SimpleNamespace:
    return SimpleNamespace(client=SimpleNamespace(host=ip), url=SimpleNamespace(path=path))


def test_rate_limiter_allows_then_blocks() -> None:
    limiter = RateLimiter(limit=2, window_seconds=60, enabled=True)
    req = _fake_request()

    asyncio.run(limiter(req))  # 1 - ok
    asyncio.run(limiter(req))  # 2 - ok
    with pytest.raises(HTTPException) as exc:
        asyncio.run(limiter(req))  # 3 - blocked
    assert exc.value.status_code == 429
    assert exc.value.headers["Retry-After"] == "60"


def test_rate_limiter_is_per_ip() -> None:
    limiter = RateLimiter(limit=1, window_seconds=60, enabled=True)
    asyncio.run(limiter(_fake_request(ip="10.0.0.1")))
    # A different IP has its own budget.
    asyncio.run(limiter(_fake_request(ip="10.0.0.2")))


def test_rate_limiter_disabled_is_noop() -> None:
    limiter = RateLimiter(limit=1, window_seconds=60, enabled=False)
    for _ in range(10):
        asyncio.run(limiter(_fake_request()))  # never raises


def test_security_headers_present() -> None:
    resp = client.get("/api/v1/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'none'" in resp.headers["Content-Security-Policy"]


def test_docs_exempt_from_strict_csp() -> None:
    # Swagger UI must be allowed to load its assets.
    resp = client.get("/openapi.json")
    assert "Content-Security-Policy" not in resp.headers
