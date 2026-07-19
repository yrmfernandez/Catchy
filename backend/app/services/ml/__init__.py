"""ML serving subpackage: load the M3 bundle and score emails."""

from app.services.ml.predictor import PhishingModel

__all__ = ["PhishingModel"]
