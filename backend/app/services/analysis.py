"""ScanService: the analysis pipeline's composition root.

The local pipeline is parse -> features -> rule score -> ML predict -> fuse. From
M5, an optional async step enriches with external threat intel before the fuse.
The LLM analyst (M6) will slot in the same way. Keeping the orchestration in one
service is what lets the routers stay trivial.
"""

from __future__ import annotations

from app.schemas.email import ParsedEmail
from app.schemas.features import FeatureVector, MLPrediction, RiskAssessment
from app.schemas.intel import ThreatIntel
from app.schemas.scan import ScanResult
from app.services.features import FeatureExtractor
from app.services.intel import ThreatIntelService
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
        intel: ThreatIntelService,
    ) -> None:
        self._parser = parser
        self._extractor = extractor
        self._scorer = scorer
        self._model = model
        self._fuser = fuser
        self._intel = intel

    def _local(
        self, raw: bytes | str
    ) -> tuple[ParsedEmail, FeatureVector, RiskAssessment, MLPrediction]:
        parsed = self._parser.parse(raw)
        features = self._extractor.extract(parsed)
        assessment = self._scorer.score(features, parsed)
        ml = self._model.predict(parsed)
        return parsed, features, assessment, ml

    def analyze(self, raw: bytes | str) -> ScanResult:
        """Synchronous local-only analysis (no external threat intel)."""
        parsed, features, assessment, ml = self._local(raw)
        intel = ThreatIntel.disabled()
        fusion = self._fuser.fuse(features, assessment, ml, intel)
        return ScanResult(
            parsed=parsed,
            features=features,
            assessment=assessment,
            ml=ml,
            intel=intel,
            fusion=fusion,
        )

    async def analyze_async(self, raw: bytes | str) -> ScanResult:
        """Full analysis including external threat-intel enrichment (when enabled)."""
        parsed, features, assessment, ml = self._local(raw)
        intel = await self._intel.enrich(parsed)
        fusion = self._fuser.fuse(features, assessment, ml, intel)
        return ScanResult(
            parsed=parsed,
            features=features,
            assessment=assessment,
            ml=ml,
            intel=intel,
            fusion=fusion,
        )
