"""LLM analyst schemas.

`LlmAnalysis` is the human-facing explanation of a scan: why it looks suspicious,
the likely attack technique, and what to do. Crucially it is *explanatory* — the
`confidence` is the model's own independent read, used only as the small AI
component of the fused score (and only ever to *raise* it). The LLM never sets
the verdict. When no provider/key is configured it is simply `available=False`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LlmAnalysisPayload(BaseModel):
    """The exact JSON shape we ask the model to return (and validate)."""

    summary: str = ""
    why_suspicious: list[str] = Field(default_factory=list)
    attack_techniques: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    confidence: float | None = Field(
        default=None, description="Model's independent P(phishing), 0-1 — reference only"
    )


class LlmAnalysis(BaseModel):
    available: bool
    provider: str | None = None
    model: str | None = None
    summary: str | None = None
    why_suspicious: list[str] = Field(default_factory=list)
    attack_techniques: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    confidence: float | None = None
    error: str | None = None

    @classmethod
    def unavailable(cls, reason: str | None = None) -> LlmAnalysis:
        return cls(available=False, error=reason)
