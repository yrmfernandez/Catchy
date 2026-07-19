"""Reputation providers. Each is independent, key-gated, and best-effort."""

from app.services.intel.providers.base import IntelContext, Provider, ProviderOutcome
from app.services.intel.providers.hibp import HibpProvider
from app.services.intel.providers.rdap import RdapProvider
from app.services.intel.providers.urlscan import UrlscanProvider
from app.services.intel.providers.virustotal import VirusTotalProvider

DEFAULT_PROVIDERS: tuple[Provider, ...] = (
    VirusTotalProvider(),
    UrlscanProvider(),
    RdapProvider(),
    HibpProvider(),
)

__all__ = [
    "IntelContext",
    "Provider",
    "ProviderOutcome",
    "VirusTotalProvider",
    "UrlscanProvider",
    "RdapProvider",
    "HibpProvider",
    "DEFAULT_PROVIDERS",
]
