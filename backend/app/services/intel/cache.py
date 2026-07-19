"""Redis-backed cache for reputation lookups.

Reputation changes slowly and the upstream APIs are strictly rate-limited, so we
cache aggressively (a day by default). The cache is *best-effort*: if Redis is
absent or unreachable we mark it broken and every operation becomes a no-op, so a
missing Redis degrades to "just call the API" (or, with intel off, nothing) rather
than an error.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("catchy.intel.cache")


class IntelCache:
    def __init__(self, redis_url: str, ttl_seconds: int) -> None:
        self._url = redis_url
        self._ttl = ttl_seconds
        self._client: Any = None
        self._broken = False

    def _redis(self) -> Any:
        if self._broken:
            return None
        if self._client is None:
            try:
                import redis.asyncio as aioredis

                self._client = aioredis.from_url(
                    self._url,
                    socket_connect_timeout=1,
                    socket_timeout=1,
                    decode_responses=True,
                )
            except Exception:  # noqa: BLE001 - any redis issue -> disable caching
                logger.warning("Redis cache unavailable; continuing without caching")
                self._broken = True
                return None
        return self._client

    async def get(self, key: str) -> Any | None:
        client = self._redis()
        if client is None:
            return None
        try:
            raw = await client.get(key)
            return json.loads(raw) if raw else None
        except Exception:  # noqa: BLE001
            self._broken = True
            return None

    async def set(self, key: str, value: Any) -> None:
        client = self._redis()
        if client is None:
            return
        try:
            await client.set(key, json.dumps(value), ex=self._ttl)
        except Exception:  # noqa: BLE001
            self._broken = True
