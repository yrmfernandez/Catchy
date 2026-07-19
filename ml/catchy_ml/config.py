"""Paths and training constants."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # ml/
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"

# The trained bundle and its metrics report.
MODEL_PATH = MODELS_DIR / "catchy_model.joblib"
METRICS_PATH = MODELS_DIR / "metrics.json"

RANDOM_SEED = 42
TEST_SIZE = 0.25
# Decision threshold on P(phish). Tuned in M4 against the fusion weights; 0.5 for now.
DEFAULT_THRESHOLD = 0.5
