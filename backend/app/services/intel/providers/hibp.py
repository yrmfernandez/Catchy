"""Have I Been Pwned: breach exposure of the sender address.

Informational (points=0): a sender address appearing in past breaches doesn't
make *this* email phishing, but it's useful context (e.g. a compromised account
sending on the attacker's behalf). Requires an HIBP API key.
"""

from __future__ import annotations

import httpx

from app.core.config import Settings
from app.schemas.features import Indicator, Severity
from app.schemas.intel import ProviderStatus
from app.services.intel.cache import IntelCache
from app.services.intel.providers.base import IntelContext, Provider, ProviderOutcome


class HibpProvider(Provider):
    name = "hibp"

    def is_enabled(self, settings: Settings) -> bool:
        return bool(settings.hibp_api_key)

    async def run(
        self, ctx: IntelContext, client: httpx.AsyncClient, cache: IntelCache, settings: Settings
    ) -> ProviderOutcome:
        if not ctx.sender_email:
            return ProviderOutcome(
                status=ProviderStatus(name=self.name, status="skipped", detail="no sender address")
            )

        count = await self._breach_count(ctx.sender_email, client, cache, settings)
        if count is None:
            return ProviderOutcome(
                status=ProviderStatus(name=self.name, status="error", detail="lookup failed")
            )

        indicators: list[Indicator] = []
        if count > 0:
            indicators.append(
                Indicator(
                    id="sender_breached",
                    title="Sender address in known breaches",
                    category="sender",
                    severity=Severity.info,
                    points=0,
                    detail=f"Sender appears in {count} known breach(es) (informational).",
                )
            )
        return self._ok(indicators=indicators, signals={"sender_breach_count": count})

    async def _breach_count(self, email, client, cache, settings) -> int | None:
        key = f"hibp:{email}"
        cached = await cache.get(key)
        if cached is not None:
            return cached.get("count")
        resp = await client.get(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
            params={"truncateResponse": "true"},
            headers={"hibp-api-key": settings.hibp_api_key},
        )
        if resp.status_code == 404:
            count = 0
        elif resp.status_code == 200:
            count = len(resp.json())
        else:
            return None
        await cache.set(key, {"count": count})
        return count
