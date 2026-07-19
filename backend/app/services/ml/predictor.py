"""PhishingModel: serve the trained classifier.

Loads the joblib bundle produced by `ml/` (M3) and turns a ParsedEmail into a
calibrated phishing probability. The featurization here MUST match training
exactly — text = subject + visible body, numeric = the FeatureVector in the
bundle's recorded column order — otherwise the model sees a different distribution
than it learned. Both sides route through the same FeatureExtractor, so only this
small glue is duplicated (deliberately, to avoid a backend->ml import).

If the model file is missing or fails to load, the model reports `available =
False` and the scorer falls back to the rule engine. A missing model must never
take the API down.
"""

from __future__ import annotations

import logging
from pathlib import Path

import scipy.sparse as sp

from app.schemas.email import ParsedEmail
from app.schemas.features import MLPrediction
from app.services.features import FeatureExtractor
from app.services.features.lexicons import strip_html

logger = logging.getLogger("catchy.ml")


class PhishingModel:
    def __init__(self, model_path: str) -> None:
        self._path = Path(model_path)
        self._extractor = FeatureExtractor()
        self._bundle: dict | None = None
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            logger.warning("ML model not found at %s — scoring will use rules only", self._path)
            return
        try:
            import joblib

            self._bundle = joblib.load(self._path)
            logger.info(
                "Loaded ML model '%s' from %s", self._bundle.get("model_type"), self._path
            )
        except Exception:
            logger.exception("Failed to load ML model at %s — falling back to rules", self._path)
            self._bundle = None

    @property
    def available(self) -> bool:
        return self._bundle is not None

    def predict(self, parsed: ParsedEmail) -> MLPrediction:
        if self._bundle is None:
            return MLPrediction(available=False)
        prob = self._probability(parsed)
        threshold = float(self._bundle.get("threshold", 0.5))
        return MLPrediction(
            available=True,
            probability=round(prob, 4),
            label="phishing" if prob >= threshold else "legit",
            model_type=self._bundle.get("model_type"),
            threshold=threshold,
        )

    def _probability(self, parsed: ParsedEmail) -> float:
        b = self._bundle
        assert b is not None
        body = parsed.body_plain or strip_html(parsed.body_html or "")
        text = f"{parsed.subject or ''}\n{body}".strip()
        fv = self._extractor.extract(parsed)
        numeric = [[float(getattr(fv, name)) for name in b["feature_names"]]]

        text_mat = b["tfidf"].transform([text])
        num_mat = b["scaler"].transform(numeric)
        X = sp.hstack([text_mat, sp.csr_matrix(num_mat)]).tocsr()
        return float(b["classifier"].predict_proba(X)[0, 1])
