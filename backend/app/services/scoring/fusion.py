"""ScoreFuser: blend the ML probability with the rule signals into one score.

The project's thesis is "combine techniques; the LLM explains, it doesn't decide".
This is where the combining happens. Each detection dimension produces a 0-100
sub-score; they are averaged using the design weights:

    ML 35 · URL 25 · sender 20 · attachment 10 · AI 10   (AI joins at M6)

Two safety properties:
  * Graceful degradation — with no ML model the weighted blend can't run, so we
    fall back to the transparent rule score rather than guessing.
  * Critical override — a confirmed-malicious indicator (e.g. an executable
    attachment) floors the final score, so one decisive signal can never be
    averaged away into a comfortable-looking number.
"""

from __future__ import annotations

from app.schemas.features import (
    FeatureVector,
    FusionComponent,
    FusionResult,
    MLPrediction,
    RiskAssessment,
    Severity,
)
from app.schemas.intel import ThreatIntel
from app.services.scoring.scorer import band_for_score

# Design weights (per the architecture). AI is present but contributes nothing
# until the LLM analyst arrives in M6; its weight is simply not in play yet.
WEIGHTS: dict[str, float] = {
    "ml": 0.35,
    "url": 0.25,
    "sender": 0.20,
    "attachment": 0.10,
    "ai": 0.10,
}


def _url_subscore(f: FeatureVector) -> float:
    score = 0.0
    if f.link_mismatch_count > 0:
        score += 60
    if f.ip_url_count > 0:
        score += 50
    if f.max_domain_entropy > 3.5:
        score += 25
    if f.url_count > 10:
        score += 15
    return min(score, 100.0)


def _sender_subscore(f: FeatureVector) -> float:
    score = 0.0
    if f.spf_fail:
        score += 45
    if f.dmarc_fail:
        score += 45
    if f.reply_to_mismatch:
        score += 40
    if f.dkim_missing:
        score += 15
    return min(score, 100.0)


def _attachment_subscore(f: FeatureVector) -> float:
    if f.risky_attachment_count > 0:
        return 100.0
    if f.attachment_count > 0:
        return 10.0
    return 0.0


class ScoreFuser:
    """Stateless; share one instance."""

    def __init__(self, critical_floor: int = 90) -> None:
        self._floor = critical_floor

    def fuse(
        self,
        features: FeatureVector,
        assessment: RiskAssessment,
        ml: MLPrediction,
        intel: ThreatIntel | None = None,
    ) -> FusionResult:
        subscores = {
            "url": _url_subscore(features),
            "sender": _sender_subscore(features),
            "attachment": _attachment_subscore(features),
        }
        # External reputation (M5) sharpens the structural sub-scores when present.
        if intel is not None and intel.available:
            self._apply_intel(subscores, intel)
        if ml.available and ml.probability is not None:
            subscores["ml"] = ml.probability * 100.0

        if "ml" in subscores:
            # Weighted blend over the present dimensions (AI still absent).
            present = {k: subscores[k] for k in ("ml", "url", "sender", "attachment")}
            wsum = sum(WEIGHTS[k] for k in present)
            raw = sum(subscores[k] * WEIGHTS[k] for k in present) / wsum
            score = round(raw)
            method = "fused"
            components = [
                FusionComponent(
                    name=k,
                    score=round(subscores[k], 1),
                    weight=round(WEIGHTS[k] / wsum, 3),
                )
                for k in present
            ]
        else:
            # No model: the rule engine is the source of truth (it also captures
            # content/urgency signals the four dimensions above don't).
            score = assessment.score
            method = "rules_only"
            components = [
                FusionComponent(name=k, score=round(subscores[k], 1), weight=WEIGHTS[k])
                for k in ("url", "sender", "attachment")
            ]

        override = any(i.severity == Severity.critical for i in assessment.indicators)
        if intel is not None:
            override = override or bool(
                intel.url_malicious_hits or intel.attachment_malicious_hits
            )
        if override:
            score = max(score, self._floor)
        score = max(0, min(100, score))

        band = band_for_score(score)
        return FusionResult(
            score=score,
            band=band,
            method=method,
            critical_override=override,
            components=components,
            summary=self._summary(band, score, method, ml, override),
        )

    @staticmethod
    def _apply_intel(subscores: dict[str, float], intel: ThreatIntel) -> None:
        if intel.url_malicious_hits > 0:
            subscores["url"] = max(subscores["url"], 95.0)
        if intel.attachment_malicious_hits > 0:
            subscores["attachment"] = 100.0
        age = intel.min_domain_age_days
        if age is not None and age < 30:
            subscores["url"] = max(subscores["url"], 70.0 if age < 7 else 55.0)

    @staticmethod
    def _summary(band, score: int, method: str, ml: MLPrediction, override: bool) -> str:
        if method == "fused" and ml.probability is not None:
            base = (
                f"{band.value.title()} risk ({score}/100) — "
                f"ML {round(ml.probability * 100)}% blended with rule signals."
            )
        else:
            base = (
                f"{band.value.title()} risk ({score}/100) — "
                "rule engine only (ML model unavailable)."
            )
        if override:
            base += " A confirmed-malicious indicator forced an elevated score."
        return base
