"""Unit tests for the score fuser (no model needed — inputs are constructed)."""

from app.schemas.features import (
    FeatureVector,
    Indicator,
    MLPrediction,
    RiskAssessment,
    RiskBand,
    Severity,
)
from app.schemas.intel import ThreatIntel
from app.services.scoring import ScoreFuser

fuser = ScoreFuser(critical_floor=90)


def _assessment(score: int, indicators=None) -> RiskAssessment:
    return RiskAssessment(
        score=score,
        band=RiskBand.low,
        summary="test",
        indicators=indicators or [],
    )


def test_fused_blend_uses_weighted_average() -> None:
    features = FeatureVector(link_mismatch_count=1, spf_fail=True)  # url=60, sender=45, attach=0
    ml = MLPrediction(available=True, probability=0.9)
    result = fuser.fuse(features, _assessment(50), ml)

    # (90*.35 + 60*.25 + 45*.20 + 0*.10) / .90 = 61.67 -> 62
    assert result.method == "fused"
    assert result.score == 62
    assert result.band == RiskBand.high
    assert {c.name for c in result.components} == {"ml", "url", "sender", "attachment"}


def test_rules_only_when_model_unavailable() -> None:
    features = FeatureVector(spf_fail=True)
    ml = MLPrediction(available=False)
    result = fuser.fuse(features, _assessment(37), ml)

    assert result.method == "rules_only"
    assert result.score == 37  # falls back to the rule score
    assert result.band == RiskBand.medium
    assert all(c.name != "ml" for c in result.components)


def test_critical_override_floors_score() -> None:
    features = FeatureVector(risky_attachment_count=1)
    ml = MLPrediction(available=True, probability=0.1)  # would otherwise be tiny
    crit = Indicator(
        id="risky_attachment",
        title="Dangerous attachment type",
        category="attachment",
        severity=Severity.critical,
        points=20,
        detail="exe",
    )
    result = fuser.fuse(features, _assessment(20, [crit]), ml)

    assert result.critical_override is True
    assert result.score >= 90
    assert result.band == RiskBand.critical


def test_score_bounds() -> None:
    ml = MLPrediction(available=True, probability=0.0)
    result = fuser.fuse(FeatureVector(), _assessment(0), ml)
    assert 0 <= result.score <= 100


def test_intel_malicious_url_forces_override() -> None:
    # A VirusTotal-confirmed malicious URL must floor the score even if the
    # ML probability and structural features look tame.
    intel = ThreatIntel(enabled=True, available=True, url_malicious_hits=1)
    ml = MLPrediction(available=True, probability=0.1)
    result = fuser.fuse(FeatureVector(), _assessment(10), ml, intel)

    assert result.critical_override is True
    assert result.score >= 90
    assert result.band == RiskBand.critical


def test_intel_young_domain_raises_score() -> None:
    features = FeatureVector()
    ml = MLPrediction(available=True, probability=0.2)
    baseline = fuser.fuse(features, _assessment(0), ml)

    intel = ThreatIntel(enabled=True, available=True, min_domain_age_days=3)
    boosted = fuser.fuse(features, _assessment(0), ml, intel)

    assert boosted.score > baseline.score
