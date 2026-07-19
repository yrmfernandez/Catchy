"""ScanService: the analysis pipeline's composition root.

The pipeline is now: parse -> extract features -> rule score -> ML predict ->
fuse. The LLM analyst (M6) will slot in as one more step that enriches the same
ScanResult. Keeping the orchestration in one service is what lets the routers
stay trivial.
"""

from __future__ import annotations

from app.schemas.scan import ScanResult
from app.services.features import FeatureExtractor
from app.services.ml import PhishingModel
from app.services.parsing import EmailParserService
from app.services.scoring import RuleScorer, ScoreFuser


class ScanService:
    def __init__(
        self,
        parser: EmailParserService,
        extractor: FeatureExtractor,
        scorer: RuleScorer,
        model: PhishingModel,
        fuser: ScoreFuser,
    ) -> None:
        self._parser = parser
        self._extractor = extractor
        self._scorer = scorer
        self._model = model
        self._fuser = fuser

    def analyze(self, raw: bytes | str) -> ScanResult:
        parsed = self._parser.parse(raw)
        features = self._extractor.extract(parsed)
        assessment = self._scorer.score(features, parsed)
        ml = self._model.predict(parsed)
        fusion = self._fuser.fuse(features, assessment, ml)
        return ScanResult(
            parsed=parsed,
            features=features,
            assessment=assessment,
            ml=ml,
            fusion=fusion,
        )
