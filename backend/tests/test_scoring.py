"""Tests for the rule-based scorer."""

from pathlib import Path

import pytest

from app.schemas.features import RiskBand
from app.services.features import FeatureExtractor
from app.services.parsing import EmailParserService
from app.services.scoring import RuleScorer

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def assess():
    parser = EmailParserService()
    extractor = FeatureExtractor()
    scorer = RuleScorer()

    def _assess(name: str):
        parsed = parser.parse((FIXTURES / name).read_bytes())
        return scorer.score(extractor.extract(parsed), parsed)

    return _assess


def test_benign_scores_low(assess) -> None:
    a = assess("benign.eml")
    assert a.band == RiskBand.low
    assert a.score < 25
    assert all(i.severity.value in {"info", "low"} for i in a.indicators)


def test_phishing_scores_high(assess) -> None:
    a = assess("phishing.eml")
    assert a.score >= 75
    assert a.band == RiskBand.critical
    ids = {i.id for i in a.indicators}
    # The marquee phishing signals must be represented.
    assert {"link_mismatch", "ip_url", "risky_attachment", "spf_fail"} <= ids


def test_indicators_sorted_and_score_capped(assess) -> None:
    a = assess("phishing.eml")
    points = [i.points for i in a.indicators]
    assert points == sorted(points, reverse=True)
    assert 0 <= a.score <= 100
    assert "Top signals" in a.summary
