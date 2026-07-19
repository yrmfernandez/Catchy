"""ScanService: the analysis pipeline's composition root.

Right now the pipeline is parse -> extract features -> rule score. Each later
milestone slots in *here* without changing the API: the ML classifier (M4) and
the LLM analyst (M6) become additional steps that enrich the same ScanResult.
Keeping the orchestration in one service is what lets the routers stay trivial.
"""

from __future__ import annotations

from app.schemas.scan import ScanResult
from app.services.features import FeatureExtractor
from app.services.parsing import EmailParserService
from app.services.scoring import RuleScorer


class ScanService:
    def __init__(
        self,
        parser: EmailParserService,
        extractor: FeatureExtractor,
        scorer: RuleScorer,
    ) -> None:
        self._parser = parser
        self._extractor = extractor
        self._scorer = scorer

    def analyze(self, raw: bytes | str) -> ScanResult:
        parsed = self._parser.parse(raw)
        features = self._extractor.extract(parsed)
        assessment = self._scorer.score(features, parsed)
        return ScanResult(parsed=parsed, features=features, assessment=assessment)
