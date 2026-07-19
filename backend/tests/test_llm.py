"""Tests for the LLM analyst (offline — a fake provider, never a real API)."""

import asyncio
from pathlib import Path

from app.core.config import Settings
from app.schemas.intel import ThreatIntel
from app.schemas.llm import LlmAnalysis
from app.schemas.scan import ScanResult
from app.services.features import FeatureExtractor
from app.services.llm.analyst import LlmAnalyst
from app.services.llm.base import LlmError, LlmProvider
from app.services.llm.prompt import build_system, build_user
from app.services.ml import PhishingModel
from app.services.parsing import EmailParserService
from app.services.scoring import RuleScorer, ScoreFuser

FIXTURES = Path(__file__).parent / "fixtures"
_settings = Settings()


def _result(name: str) -> ScanResult:
    parser, extractor, scorer, fuser = (
        EmailParserService(),
        FeatureExtractor(),
        RuleScorer(),
        ScoreFuser(),
    )
    parsed = parser.parse((FIXTURES / name).read_bytes())
    features = extractor.extract(parsed)
    assessment = scorer.score(features, parsed)
    ml = PhishingModel("nope.joblib").predict(parsed)  # unavailable
    fusion = fuser.fuse(features, assessment, ml)
    return ScanResult(
        parsed=parsed,
        features=features,
        assessment=assessment,
        ml=ml,
        intel=ThreatIntel.disabled(),
        analysis=LlmAnalysis.unavailable(),
        fusion=fusion,
    )


class _FakeProvider(LlmProvider):
    name = "fake"
    model = "fake-1"

    def __init__(self, text: str | None = None, exc: Exception | None = None) -> None:
        self._text = text
        self._exc = exc
        self.last_user: str | None = None

    async def complete(self, system: str, user: str) -> str:
        self.last_user = user
        if self._exc:
            raise self._exc
        return self._text or ""


_GOOD_JSON = (
    '{"summary": "Spoofed sender with a mismatched link.", '
    '"why_suspicious": ["SPF failed", "link text does not match href"], '
    '"attack_techniques": ["credential harvesting"], '
    '"recommendations": ["Do not click", "Report to IT"], '
    '"confidence": 0.94}'
)


def test_unavailable_without_provider() -> None:
    analyst = LlmAnalyst(None, _settings)
    out = asyncio.run(analyst.analyze(_result("phishing.eml")))
    assert out.available is False
    assert out.error


def test_parses_valid_json() -> None:
    analyst = LlmAnalyst(_FakeProvider(_GOOD_JSON), _settings)
    out = asyncio.run(analyst.analyze(_result("phishing.eml")))
    assert out.available is True
    assert out.provider == "fake"
    assert out.confidence == 0.94
    assert "credential harvesting" in out.attack_techniques
    assert len(out.recommendations) == 2


def test_parses_json_wrapped_in_code_fence() -> None:
    analyst = LlmAnalyst(_FakeProvider(f"```json\n{_GOOD_JSON}\n```"), _settings)
    out = asyncio.run(analyst.analyze(_result("phishing.eml")))
    assert out.available is True
    assert out.confidence == 0.94


def test_provider_error_degrades() -> None:
    analyst = LlmAnalyst(_FakeProvider(exc=LlmError("boom")), _settings)
    out = asyncio.run(analyst.analyze(_result("phishing.eml")))
    assert out.available is False


def test_unparseable_output_degrades() -> None:
    analyst = LlmAnalyst(_FakeProvider("not json at all"), _settings)
    out = asyncio.run(analyst.analyze(_result("phishing.eml")))
    assert out.available is False


def test_prompt_isolates_untrusted_email() -> None:
    # The system rules and the sentinel delimiting are the injection defense.
    system = build_system()
    assert "UNTRUSTED" in system
    assert "do NOT decide or change the verdict" in system or "final" in system

    fake = _FakeProvider(_GOOD_JSON)
    asyncio.run(LlmAnalyst(fake, _settings).analyze(_result("phishing.eml")))
    assert fake.last_user is not None
    assert "<<<UNTRUSTED_EMAIL_BEGIN>>>" in fake.last_user
    assert "<<<UNTRUSTED_EMAIL_END>>>" in fake.last_user


def test_prompt_truncates_long_bodies() -> None:
    result = _result("phishing.eml")
    user = build_user(result, max_chars=10)
    assert "[truncated]" in user
