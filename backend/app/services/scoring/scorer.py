"""RuleScorer: run the rules, sum the points, produce a RiskAssessment.

The score is capped at 100 and mapped to a band. Because every point is traceable
to a named indicator, the assessment is fully explainable — there is no hidden
term. When the ML model arrives (M4) its probability fuses in as one more
weighted contributor alongside these rules, never as a silent override.
"""

from __future__ import annotations

from app.schemas.email import ParsedEmail
from app.schemas.features import FeatureVector, Indicator, RiskAssessment, RiskBand
from app.services.scoring.rules import RULES

# Score thresholds -> band. Tuned so any single high-severity rule lands at least
# in "medium", and a couple of strong signals reach "high"/"critical". Shared by
# the rule scorer and the M4 fuser so both speak the same language.
_BANDS: tuple[tuple[int, RiskBand], ...] = (
    (75, RiskBand.critical),
    (50, RiskBand.high),
    (25, RiskBand.medium),
    (0, RiskBand.low),
)


def band_for_score(score: int) -> RiskBand:
    for threshold, band in _BANDS:
        if score >= threshold:
            return band
    return RiskBand.low


class RuleScorer:
    """Stateless; share one instance."""

    def score(self, features: FeatureVector, parsed: ParsedEmail) -> RiskAssessment:
        indicators = [ind for rule in RULES if (ind := rule(features, parsed)) is not None]
        indicators.sort(key=lambda i: i.points, reverse=True)

        total = min(sum(i.points for i in indicators), 100)
        band = band_for_score(total)
        return RiskAssessment(
            score=total,
            band=band,
            summary=self._summary(band, indicators),
            indicators=indicators,
        )

    @staticmethod
    def _summary(band: RiskBand, indicators: list[Indicator]) -> str:
        headline = {
            RiskBand.critical: "Critical risk — strong phishing indicators.",
            RiskBand.high: "High risk — multiple phishing indicators.",
            RiskBand.medium: "Medium risk — some suspicious traits.",
            RiskBand.low: "Low risk — no strong phishing indicators.",
        }[band]
        if not indicators:
            return headline
        top = "; ".join(i.title for i in indicators[:3])
        return f"{headline} Top signals: {top}."
