"""Tests for ML serving and its graceful degradation."""

from pathlib import Path

import pytest

from app.core.config import get_settings
from app.services.ml import PhishingModel
from app.services.parsing import EmailParserService

FIXTURES = Path(__file__).parent / "fixtures"
_parser = EmailParserService()


def test_missing_model_degrades_gracefully() -> None:
    model = PhishingModel("this/path/does/not/exist.joblib")
    assert model.available is False

    parsed = _parser.parse((FIXTURES / "phishing.eml").read_bytes())
    pred = model.predict(parsed)
    assert pred.available is False
    assert pred.probability is None


_MODEL_PATH = Path(get_settings().model_path)


@pytest.mark.skipif(not _MODEL_PATH.exists(), reason="no trained model present (run ml/ training)")
def test_trained_model_scores_phish_above_legit() -> None:
    model = PhishingModel(str(_MODEL_PATH))
    assert model.available is True

    phish = model.predict(_parser.parse((FIXTURES / "phishing.eml").read_bytes()))
    legit = model.predict(_parser.parse((FIXTURES / "benign.eml").read_bytes()))

    assert phish.probability is not None and legit.probability is not None
    assert phish.probability > legit.probability
    assert phish.label == "phishing"
