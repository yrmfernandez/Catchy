"""The composite scan result: parsing + features + assessment.

This is what `POST /scan/analyze` returns and, from M7, what gets persisted per
scan. Bundling the three layers keeps the API honest — the caller sees the raw
evidence (parsed), the derived numbers (features), and the verdict (assessment)
together, so a score is never presented without the reasons behind it.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.email import ParsedEmail
from app.schemas.features import (
    FeatureVector,
    FusionResult,
    MLPrediction,
    RiskAssessment,
)


class ScanResult(BaseModel):
    parsed: ParsedEmail
    features: FeatureVector
    assessment: RiskAssessment  # rule engine (M2) — always present, fully explainable
    ml: MLPrediction  # classifier (M3/M4) — may be unavailable
    fusion: FusionResult  # final blended score (M4); fusion.score is the headline number
