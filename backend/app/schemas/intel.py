"""Threat-intelligence schemas.

`ThreatIntel` is the normalized result of asking external reputation sources
(VirusTotal, URLScan, RDAP/WHOIS, Have I Been Pwned) about an email's URLs,
domains, attachments, and sender. It is *always present* in a ScanResult — when
enrichment is disabled or unreachable it is simply `enabled=False /
available=False`, so the rest of the pipeline never has to special-case it.

The per-provider `status` list makes degradation observable: a reader can see
exactly which sources answered, which were skipped for lack of a key, and which
errored or timed out.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.features import Indicator


class ProviderStatus(BaseModel):
    name: str
    status: str = Field(description="ok | disabled | no_key | error | timeout | skipped")
    detail: str | None = None


class ThreatIntel(BaseModel):
    enabled: bool = False
    available: bool = Field(default=False, description="At least one provider returned data")
    providers: list[ProviderStatus] = Field(default_factory=list)
    indicators: list[Indicator] = Field(
        default_factory=list, description="Reputation findings that feed the score"
    )

    # Normalized signals consumed by the fuser.
    url_malicious_hits: int = Field(default=0, description="URLs flagged malicious by reputation")
    attachment_malicious_hits: int = Field(default=0, description="Attachment hashes flagged")
    min_domain_age_days: int | None = Field(
        default=None, description="Age of the youngest linked domain (freshly-registered = risky)"
    )
    sender_breach_count: int | None = Field(
        default=None, description="HIBP breaches for the sender address (informational)"
    )

    @classmethod
    def disabled(cls) -> ThreatIntel:
        return cls(enabled=False, available=False)
