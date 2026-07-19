"""Tests for threat-intel enrichment (offline — no real providers called)."""

import asyncio

from app.core.config import Settings
from app.schemas.email import EmailAddress, ExtractedUrl, ParsedEmail
from app.services.intel import ThreatIntelService
from app.services.intel.cache import IntelCache
from app.services.intel.providers.base import IntelContext, Provider, ProviderOutcome

# A redis URL pointing at a closed port — exercises the graceful-fallback path.
_DEAD_REDIS = "redis://127.0.0.1:1/0"


def _parsed() -> ParsedEmail:
    return ParsedEmail(
        subject="hello",
        **{"from": EmailAddress(raw="a@b.com", address="a@b.com", domain="b.com")},
        urls=[ExtractedUrl(url="http://x.com/p", domain="x.com")],
    )


def test_intel_disabled_by_default() -> None:
    svc = ThreatIntelService(Settings(intel_enabled=False), IntelCache(_DEAD_REDIS, 10))
    result = asyncio.run(svc.enrich(_parsed()))

    assert result.enabled is False
    assert result.available is False
    assert result.providers  # every provider reported as disabled
    assert all(p.status == "disabled" for p in result.providers)


class _DummyProvider(Provider):
    name = "dummy"

    def is_enabled(self, settings: Settings) -> bool:
        return True

    async def run(self, ctx: IntelContext, client, cache, settings) -> ProviderOutcome:
        return self._ok(signals={"url_malicious_hits": 1, "min_domain_age_days": 3})


def test_enabled_merges_provider_signals() -> None:
    svc = ThreatIntelService(
        Settings(intel_enabled=True), IntelCache(_DEAD_REDIS, 10), providers=(_DummyProvider(),)
    )
    result = asyncio.run(svc.enrich(_parsed()))

    assert result.enabled is True
    assert result.available is True
    assert result.url_malicious_hits == 1
    assert result.min_domain_age_days == 3


class _ExplodingProvider(Provider):
    name = "boom"

    def is_enabled(self, settings: Settings) -> bool:
        return True

    async def run(self, ctx: IntelContext, client, cache, settings) -> ProviderOutcome:
        raise RuntimeError("provider blew up")


def test_provider_failure_is_isolated() -> None:
    svc = ThreatIntelService(
        Settings(intel_enabled=True), IntelCache(_DEAD_REDIS, 10), providers=(_ExplodingProvider(),)
    )
    result = asyncio.run(svc.enrich(_parsed()))

    # The scan survives; the bad provider is recorded as an error.
    assert result.available is False
    assert any(p.name == "boom" and p.status == "error" for p in result.providers)


def test_cache_degrades_when_redis_unreachable() -> None:
    cache = IntelCache(_DEAD_REDIS, 10)
    assert asyncio.run(cache.get("some-key")) is None
    asyncio.run(cache.set("some-key", {"v": 1}))  # must not raise
