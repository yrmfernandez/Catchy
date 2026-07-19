"""Provider contract and shared value objects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.core.config import Settings
from app.schemas.features import Indicator
from app.schemas.intel import ProviderStatus
from app.services.intel.cache import IntelCache


@dataclass
class IntelContext:
    """The lookup targets extracted from one email."""

    urls: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    sender_email: str | None = None
    sender_domain: str | None = None
    attachment_sha256: list[str] = field(default_factory=list)


@dataclass
class ProviderOutcome:
    """What a provider returns: a status, any findings, and partial signals."""

    status: ProviderStatus
    indicators: list[Indicator] = field(default_factory=list)
    signals: dict[str, Any] = field(default_factory=dict)


class Provider(ABC):
    name: str

    @abstractmethod
    def is_enabled(self, settings: Settings) -> bool:
        """Whether this provider has what it needs to run (usually an API key)."""

    @abstractmethod
    async def run(
        self,
        ctx: IntelContext,
        client: httpx.AsyncClient,
        cache: IntelCache,
        settings: Settings,
    ) -> ProviderOutcome:
        """Perform the lookup. Must not raise for expected failures."""

    def _ok(self, **kwargs: Any) -> ProviderOutcome:
        return ProviderOutcome(status=ProviderStatus(name=self.name, status="ok"), **kwargs)
