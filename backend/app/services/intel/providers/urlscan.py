"""URLScan: whether a domain has been submitted/scanned publicly.

We use the public search API for visibility only — presence in URLScan is
informational (points=0), not a malicious verdict (which would require fetching
each result's report). It surfaces useful context without over-claiming.
"""

from __future__ import annotations

import httpx

from app.core.config import Settings
from app.schemas.features import Indicator, Severity
from app.services.intel.cache import IntelCache
from app.services.intel.providers.base import IntelContext, Provider, ProviderOutcome


class UrlscanProvider(Provider):
    name = "urlscan"

    def is_enabled(self, settings: Settings) -> bool:
        return bool(settings.urlscan_api_key)

    async def run(
        self, ctx: IntelContext, client: httpx.AsyncClient, cache: IntelCache, settings: Settings
    ) -> ProviderOutcome:
        headers = {"API-Key": settings.urlscan_api_key}
        indicators: list[Indicator] = []

        for domain in ctx.domains[: settings.intel_max_urls]:
            total = await self._search_count(domain, client, cache, headers)
            if total and total > 0:
                indicators.append(
                    Indicator(
                        id="urlscan_seen",
                        title="Domain seen on URLScan",
                        category="url",
                        severity=Severity.info,
                        points=0,
                        detail=f"{domain} appears in {total} recent URLScan submission(s).",
                    )
                )
        return self._ok(indicators=indicators)

    async def _search_count(self, domain, client, cache, headers) -> int | None:
        key = f"urlscan:{domain}"
        cached = await cache.get(key)
        if cached is not None:
            return cached.get("total")
        resp = await client.get(
            "https://urlscan.io/api/v1/search/",
            params={"q": f"domain:{domain}", "size": 1},
            headers=headers,
        )
        if resp.status_code != 200:
            return None
        total = int(resp.json().get("total", 0))
        await cache.set(key, {"total": total})
        return total
