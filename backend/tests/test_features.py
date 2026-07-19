"""Tests for feature extraction, driven by the shared .eml fixtures."""

from pathlib import Path

import pytest

from app.services.features import FeatureExtractor
from app.services.features.lexicons import shannon_entropy
from app.services.parsing import EmailParserService

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def extract():
    parser = EmailParserService()
    extractor = FeatureExtractor()
    return lambda name: extractor.extract(parser.parse((FIXTURES / name).read_bytes()))


def test_benign_features_are_clean(extract) -> None:
    f = extract("benign.eml")
    assert f.spf_fail is False
    assert f.dmarc_fail is False
    assert f.dkim_missing is False
    assert f.reply_to_mismatch is False
    assert f.link_mismatch_count == 0
    assert f.ip_url_count == 0
    assert f.risky_attachment_count == 0


def test_phishing_features_capture_signals(extract) -> None:
    f = extract("phishing.eml")
    assert f.spf_fail is True
    assert f.dmarc_fail is True
    assert f.dkim_missing is True
    assert f.reply_to_mismatch is True
    assert f.link_mismatch_count == 1
    assert f.ip_url_count >= 1
    assert f.risky_attachment_count == 1
    assert f.suspicious_keyword_count >= 1
    assert f.urgency_score > 0
    assert 0.0 <= f.html_ratio <= 1.0


def test_capital_ratio_and_entropy_helpers() -> None:
    assert shannon_entropy("") == 0.0
    assert shannon_entropy("aaaa") == 0.0
    # A varied/random string has higher entropy than a repetitive one.
    assert shannon_entropy("x7f3q9zk") > shannon_entropy("aaaaaaaa")
