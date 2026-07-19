"""ScanService: the analysis pipeline's composition root.

Full pipeline: parse -> features -> rule score -> ML predict -> threat intel ->
preliminary fuse -> LLM explanation -> final fuse. The LLM runs on the
*preliminary* verdict (so it explains a score that already exists), then its
confidence is folded back in for the final, escalate-only fuse. Keeping the
orchestration here lets the routers stay trivial.
"""

from __future__ import annotations

from app.schemas.email import ParsedEmail
from app.schemas.features import FeatureVector, MLPrediction, RiskAssessment
from app.schemas.intel import ThreatIntel
from app.schemas.llm import LlmAnalysis
from app.schemas.scan import ScanResult
from app.services.features import FeatureExtractor
from app.services.intel import ThreatIntelService
from app.services.llm import LlmAnalyst
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
        analyst: LlmAnalyst,
    ) -> None:
        self._parser = parser
        self._extractor = extractor
        self._scorer = scorer
        self._model = model
        self._fuser = fuser
        self._intel = intel
        self._analyst = analyst

    def _local(
        self, raw: bytes | str
    ) -> tuple[ParsedEmail, FeatureVector, RiskAssessment, MLPrediction]:
        parsed = self._parser.parse(raw)
        features = self._extractor.extract(parsed)
        assessment = self._scorer.score(features, parsed)
        ml = self._model.predict(parsed)
        return parsed, features, assessment, ml

    def analyze(self, raw: bytes | str) -> ScanResult:
        """Synchronous local-only analysis (no external intel, no LLM)."""
        parsed, features, assessment, ml = self._local(raw)
        intel = ThreatIntel.disabled()
        fusion = self._fuser.fuse(features, assessment, ml, intel)
        return ScanResult(
            parsed=parsed,
            features=features,
            assessment=assessment,
            ml=ml,
            intel=intel,
            analysis=LlmAnalysis.unavailable(),
            fusion=fusion,
        )

    async def analyze_async(self, raw: bytes | str) -> ScanResult:
        """Full analysis: threat-intel enrichment + LLM explanation."""
        parsed, features, assessment, ml = self._local(raw)
        intel = await self._intel.enrich(parsed)

        # Preliminary verdict (no AI weight) so the LLM explains an existing score.
        prelim_fusion = self._fuser.fuse(features, assessment, ml, intel)
        prelim = ScanResult(
            parsed=parsed,
            features=features,
            assessment=assessment,
            ml=ml,
            intel=intel,
            analysis=LlmAnalysis.unavailable(),
            fusion=prelim_fusion,
        )

        analysis = await self._analyst.analyze(prelim)

        # Final fuse folds the LLM confidence in (escalate-only).
        fusion = self._fuser.fuse(features, assessment, ml, intel, analysis)
        return prelim.model_copy(update={"analysis": analysis, "fusion": fusion})
