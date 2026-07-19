"""Feature and risk-assessment schemas.

`FeatureVector` is the numeric, ML-ready view of an email — every field is an
int/float/bool so it can be turned straight into a model input row in M3/M4. The
*same* extractor produces it at training time and inference time, which is what
keeps the two from drifting apart (train/serve skew).

`RiskAssessment` is the human-facing, explainable output of the rule engine: a
0-100 score plus the individual indicators that produced it. Later, the ML
probability and the LLM narrative fuse in alongside these rule indicators — they
never silently replace them.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class FeatureVector(BaseModel):
    """Numeric features derived deterministically from a ParsedEmail."""

    # URLs / links
    url_count: int = 0
    unique_domain_count: int = 0
    ip_url_count: int = 0
    link_mismatch_count: int = 0
    max_domain_entropy: float = Field(
        default=0.0, description="Highest Shannon entropy across link domains (DGA/random signal)"
    )

    # Authentication
    spf_fail: bool = False
    dkim_missing: bool = False
    dmarc_fail: bool = False
    reply_to_mismatch: bool = False

    # Attachments
    attachment_count: int = 0
    risky_attachment_count: int = Field(
        default=0, description="Attachments with executable/script/double extensions"
    )

    # Content / language
    suspicious_keyword_count: int = 0
    urgency_score: float = Field(default=0.0, description="0-1, density of urgency cues")
    capital_ratio: float = Field(default=0.0, description="0-1, uppercase share of letters")
    exclamation_count: int = 0
    html_ratio: float = Field(
        default=0.0, description="0-1, HTML share of the body (html vs text length)"
    )
    body_length: int = 0


class Severity(StrEnum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RiskBand(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Indicator(BaseModel):
    """One triggered rule: what fired, how bad, and why (in plain English)."""

    id: str
    title: str
    category: str = Field(description="auth | url | sender | attachment | content")
    severity: Severity
    points: int = Field(description="Contribution to the rule score")
    detail: str = Field(description="Human-readable explanation of the evidence")


class RiskAssessment(BaseModel):
    """The rule engine's verdict — fully explainable, no black box."""

    score: int = Field(ge=0, le=100, description="Rule-based risk score, 0-100")
    band: RiskBand
    summary: str = Field(description="One-line, rule-derived summary (not LLM-generated)")
    indicators: list[Indicator] = Field(default_factory=list)
