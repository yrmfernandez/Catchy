"""Turn raw emails into model inputs.

Two branches, combined downstream:
  * text  -> TF-IDF (captures wording/lures the rule lexicons miss)
  * numeric -> the production FeatureExtractor's FeatureVector (structural signals)

`parsed_to_text` and the numeric vector are the *only* transformation from email
to model input. M4's serving path reproduces these same two steps, so training
and inference stay identical.
"""

from __future__ import annotations

import numpy as np

from catchy_ml._backend import (
    EmailParserService,
    FeatureExtractor,
    FeatureVector,
    strip_html,
)

# Stable, explicit ordering of the numeric columns (matches FeatureVector).
FEATURE_NAMES: list[str] = list(FeatureVector.model_fields)

_parser = EmailParserService()
_extractor = FeatureExtractor()


def parsed_to_text(parsed) -> str:
    """Subject + visible body — the text the TF-IDF branch sees."""
    body = parsed.body_plain or strip_html(parsed.body_html or "")
    return f"{parsed.subject or ''}\n{body}".strip()


def email_to_row(raw: bytes | str) -> tuple[str, list[float]]:
    """One raw email -> (text, numeric feature list) in FEATURE_NAMES order."""
    parsed = _parser.parse(raw)
    text = parsed_to_text(parsed)
    fv = _extractor.extract(parsed)
    numeric = [float(getattr(fv, name)) for name in FEATURE_NAMES]
    return text, numeric


def build_matrices(raws: list[bytes | str]) -> tuple[list[str], np.ndarray]:
    """Vectorise a list of raw emails into (texts, numeric matrix)."""
    texts: list[str] = []
    numerics: list[list[float]] = []
    for raw in raws:
        text, numeric = email_to_row(raw)
        texts.append(text)
        numerics.append(numeric)
    return texts, np.asarray(numerics, dtype=np.float64)
