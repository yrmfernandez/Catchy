"""Bridge to the backend package.

The ML pipeline must featurize emails with the *same* code that runs in
production — otherwise the model trains on one distribution and scores on
another (train/serve skew), the classic silent ML failure. In this monorepo
`backend/` is a sibling of `ml/`, so we add it to sys.path and import the real
parser + FeatureExtractor rather than reimplementing them here.
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[2] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# Imported after the path insert on purpose.
from app.schemas.features import FeatureVector  # noqa: E402
from app.services.features import FeatureExtractor  # noqa: E402
from app.services.features.lexicons import strip_html  # noqa: E402
from app.services.parsing import EmailParserService  # noqa: E402

__all__ = ["EmailParserService", "FeatureExtractor", "FeatureVector", "strip_html"]
