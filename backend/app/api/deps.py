"""Shared FastAPI dependencies.

Providers here are injected into routers with `Depends(...)`. Keeping construction
in one place is our dependency-injection seam: tests (and later milestones) can
override any provider without touching route code. The ML model is loaded once at
process start (a missing model is fine — it degrades to rule-only scoring).
"""

from __future__ import annotations

from app.core.config import get_settings
from app.services.analysis import ScanService
from app.services.features import FeatureExtractor
from app.services.intel import ThreatIntelService
from app.services.intel.cache import IntelCache
from app.services.ml import PhishingModel
from app.services.parsing import EmailParserService
from app.services.scoring import RuleScorer, ScoreFuser

_settings = get_settings()

# Stateless singletons.
_email_parser = EmailParserService()
_feature_extractor = FeatureExtractor()
_rule_scorer = RuleScorer()
_phishing_model = PhishingModel(_settings.model_path)
_score_fuser = ScoreFuser(critical_floor=_settings.critical_override_floor)
_intel_cache = IntelCache(_settings.redis_url, _settings.intel_cache_ttl_seconds)
_intel_service = ThreatIntelService(_settings, _intel_cache)
_scan_service = ScanService(
    _email_parser,
    _feature_extractor,
    _rule_scorer,
    _phishing_model,
    _score_fuser,
    _intel_service,
)


def get_email_parser() -> EmailParserService:
    return _email_parser


def get_scan_service() -> ScanService:
    return _scan_service
