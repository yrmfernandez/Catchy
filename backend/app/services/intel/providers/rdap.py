"""RDAP: domain registration age.

No API key required (RDAP is the open successor to WHOIS), so this is the one
provider that actually runs whenever intel is enabled. A domain registered days
ago is a strong phishing signal — legitimate brands don't email you from a
week-old domain.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from app.core.config import Settings
from app.schemas.features import Indicator, Severity
from app.services.intel.cache import IntelCache
from app.services.intel.providers.base import IntelContext, Provider, ProviderOutcome


class RdapProvider(Provider):
    name = "rdap"

    def is_enabled(self, settings: Settings) -> bool:
        return True  # open protocol, no key needed

    async def run(
        self, ctx: IntelContext, client: httpx.AsyncClient, cache: IntelCache, settings: Settings
    ) -> ProviderOutcome:
        indicators: list[Indicator] = []
        min_age: int | None = None

        for domain in ctx.domains[: settings.intel_max_urls]:
            age = await self._age_days(domain, client, cache)
            if age is None:
                continue
            min_age = age if min_age is None else min(min_age, age)
            if age < 30:
                indicators.append(
                    Indicator(
                        id="young_domain",
                        title="Newly-registered domain",
                        category="url",
                        severity=Severity.high if age < 7 else Severity.medium,
                        points=25 if age < 7 else 15,
                        detail=f"{domain} was registered {age} day(s) ago.",
                    )
                )

        signals = {} if min_age is None else {"min_domain_age_days": min_age}
        return self._ok(indicators=indicators, signals=signals)

    async def _age_days(self, domain, client, cache) -> int | None:
        key = f"rdap:{domain}"
        cached = await cache.get(key)
        if cached is not None:
            return cached.get("age_days")
        resp = await client.get(f"https://rdap.org/domain/{domain}", follow_redirects=True)
        if resp.status_code != 200:
            return None
        reg = next(
            (e for e in resp.json().get("events", []) if e.get("eventAction") == "registration"),
            None,
        )
        if not reg or "eventDate" not in reg:
            return None
        try:
            registered = datetime.fromisoformat(reg["eventDate"].replace("Z", "+00:00"))
        except ValueError:
            return None
        age = (datetime.now(UTC) - registered).days
        await cache.set(key, {"age_days": age})
        return age
