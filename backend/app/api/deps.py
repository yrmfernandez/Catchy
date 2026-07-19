"""Shared FastAPI dependencies.

Providers here are injected into routers with `Depends(...)`. Keeping construction
in one place is our dependency-injection seam: tests (and later milestones) can
override any provider without touching route code.
"""

from __future__ import annotations

from app.services.analysis import ScanService
from app.services.features import FeatureExtractor
from app.services.parsing import EmailParserService
from app.services.scoring import RuleScorer

# All of these are stateless, so a single shared instance of each is fine.
_email_parser = EmailParserService()
_feature_extractor = FeatureExtractor()
_rule_scorer = RuleScorer()
_scan_service = ScanService(_email_parser, _feature_extractor, _rule_scorer)


def get_email_parser() -> EmailParserService:
    return _email_parser


def get_scan_service() -> ScanService:
    return _scan_service
