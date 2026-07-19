"""ThreatIntelService: run the providers and normalize their answers.

Enrichment is disabled unless `intel_enabled` is set. When on, enabled providers
run concurrently, each bounded by a per-call timeout; a provider that times out or
errors is recorded as such and simply contributes nothing. The merged result is a
single ThreatIntel object the fuser can consume.
"""

from __future__ import annotations

import asyncio
import logging

from app.core.config import Settings
from app.schemas.email import ParsedEmail
from app.schemas.intel import ProviderStatus, ThreatIntel
from app.services.intel.cache import IntelCache
from app.services.intel.providers import DEFAULT_PROVIDERS, IntelContext, Provider, ProviderOutcome

logger = logging.getLogger("catchy.intel")


class ThreatIntelService:
    def __init__(
        self,
        settings: Settings,
        cache: IntelCache,
        providers: tuple[Provider, ...] = DEFAULT_PROVIDERS,
    ) -> None:
        self._settings = settings
        self._cache = cache
        self._providers = providers

    async def enrich(self, parsed: ParsedEmail) -> ThreatIntel:
        if not self._settings.intel_enabled:
            return ThreatIntel(
                enabled=False,
                available=False,
                providers=[ProviderStatus(name=p.name, status="disabled") for p in self._providers],
            )

        ctx = self._context(parsed)
        enabled = [p for p in self._providers if p.is_enabled(self._settings)]
        skipped = [
            ProviderStatus(name=p.name, status="no_key")
            for p in self._providers
            if p not in enabled
        ]

        import httpx

        outcomes: list[ProviderOutcome] = []
        async with httpx.AsyncClient(
            timeout=self._settings.intel_provider_timeout_seconds,
            headers={"User-Agent": "Catchy/0.1 (+threat-intel)"},
        ) as client:
            outcomes = await asyncio.gather(
                *(self._run_guarded(p, ctx, client) for p in enabled)
            )

        return self._merge(outcomes, skipped)

    # -- internals -----------------------------------------------------------

    def _context(self, parsed: ParsedEmail) -> IntelContext:
        urls, domains, seen = [], [], set()
        for u in parsed.urls[: self._settings.intel_max_urls]:
            urls.append(u.url)
            if u.domain and not u.is_ip and u.domain not in seen:
                seen.add(u.domain)
                domains.append(u.domain)
        sender = parsed.from_address
        return IntelContext(
            urls=urls,
            domains=domains,
            sender_email=sender.address if sender else None,
            sender_domain=sender.domain if sender else None,
            attachment_sha256=[a.sha256 for a in parsed.attachments if a.sha256],
        )

    async def _run_guarded(self, provider: Provider, ctx, client) -> ProviderOutcome:
        try:
            return await asyncio.wait_for(
                provider.run(ctx, client, self._cache, self._settings),
                timeout=self._settings.intel_provider_timeout_seconds + 1,
            )
        except TimeoutError:
            return ProviderOutcome(status=ProviderStatus(name=provider.name, status="timeout"))
        except Exception as exc:  # noqa: BLE001 - one bad provider must not fail the scan
            logger.warning("intel provider %s failed: %s", provider.name, exc)
            return ProviderOutcome(
                status=ProviderStatus(name=provider.name, status="error", detail=str(exc)[:200])
            )

    @staticmethod
    def _merge(outcomes: list[ProviderOutcome], skipped: list[ProviderStatus]) -> ThreatIntel:
        result = ThreatIntel(enabled=True, providers=list(skipped))
        min_age: int | None = None
        for outcome in outcomes:
            result.providers.append(outcome.status)
            result.indicators.extend(outcome.indicators)
            sig = outcome.signals
            result.url_malicious_hits += sig.get("url_malicious_hits", 0)
            result.attachment_malicious_hits += sig.get("attachment_malicious_hits", 0)
            if (age := sig.get("min_domain_age_days")) is not None:
                min_age = age if min_age is None else min(min_age, age)
            if (breaches := sig.get("sender_breach_count")) is not None:
                result.sender_breach_count = breaches
        result.min_domain_age_days = min_age
        result.available = any(o.status.status == "ok" for o in outcomes)
        return result
