"""VirusTotal: URL and file-hash reputation (API v3).

A URL or attachment hash flagged by multiple engines is about as close to
"confirmed malicious" as external intel gets, so these findings are critical and
heavily weighted — they should push a scan to the top of the range.
"""

from __future__ import annotations

import base64

import httpx

from app.core.config import Settings
from app.schemas.features import Indicator, Severity
from app.services.intel.cache import IntelCache
from app.services.intel.providers.base import IntelContext, Provider, ProviderOutcome

_BASE = "https://www.virustotal.com/api/v3"


class VirusTotalProvider(Provider):
    name = "virustotal"

    def is_enabled(self, settings: Settings) -> bool:
        return bool(settings.virustotal_api_key)

    async def run(
        self, ctx: IntelContext, client: httpx.AsyncClient, cache: IntelCache, settings: Settings
    ) -> ProviderOutcome:
        headers = {"x-apikey": settings.virustotal_api_key}
        indicators: list[Indicator] = []
        url_hits = 0
        att_hits = 0

        for url in ctx.urls[: settings.intel_max_urls]:
            stats = await self._url_stats(url, client, cache, headers)
            if stats and stats.get("malicious", 0) > 0:
                url_hits += 1
                indicators.append(
                    Indicator(
                        id="vt_url_malicious",
                        title="URL flagged by VirusTotal",
                        category="url",
                        severity=Severity.critical,
                        points=40,
                        detail=f"{stats['malicious']} engines flagged {url} as malicious.",
                    )
                )

        for sha in ctx.attachment_sha256:
            stats = await self._file_stats(sha, client, cache, headers)
            if stats and stats.get("malicious", 0) > 0:
                att_hits += 1
                indicators.append(
                    Indicator(
                        id="vt_file_malicious",
                        title="Attachment flagged by VirusTotal",
                        category="attachment",
                        severity=Severity.critical,
                        points=60,
                        detail=f"{stats['malicious']} engines flagged attachment {sha[:12]}….",
                    )
                )

        return self._ok(
            indicators=indicators,
            signals={"url_malicious_hits": url_hits, "attachment_malicious_hits": att_hits},
        )

    async def _url_stats(self, url, client, cache, headers) -> dict | None:
        key = f"vt:url:{url}"
        cached = await cache.get(key)
        if cached is not None:
            return cached
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        resp = await client.get(f"{_BASE}/urls/{url_id}", headers=headers)
        if resp.status_code != 200:
            return None
        stats = resp.json().get("data", {}).get("attributes", {}).get("last_analysis_stats")
        if stats is not None:
            await cache.set(key, stats)
        return stats

    async def _file_stats(self, sha256, client, cache, headers) -> dict | None:
        key = f"vt:file:{sha256}"
        cached = await cache.get(key)
        if cached is not None:
            return cached
        resp = await client.get(f"{_BASE}/files/{sha256}", headers=headers)
        if resp.status_code != 200:
            return None
        stats = resp.json().get("data", {}).get("attributes", {}).get("last_analysis_stats")
        if stats is not None:
            await cache.set(key, stats)
        return stats
