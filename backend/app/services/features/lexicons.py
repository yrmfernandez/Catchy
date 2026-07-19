"""Word lists and small text utilities used by feature extraction.

These lexicons are intentionally simple and transparent — a reviewer can read
exactly what the rule engine reacts to. They are curated from common phishing
lures (credential theft, urgency, financial hooks). The ML model in M3 learns
subtler patterns; these lists power the explainable rule layer.
"""

from __future__ import annotations

import math
import re

# Cues that create false time pressure ("act now or lose access").
URGENCY_TERMS: frozenset[str] = frozenset(
    {
        "urgent",
        "immediately",
        "act now",
        "right away",
        "as soon as possible",
        "asap",
        "within 24 hours",
        "within 48 hours",
        "expires",
        "expiring",
        "expire",
        "final notice",
        "last warning",
        "suspended",
        "suspension",
        "limited",
        "deadline",
        "verify now",
        "action required",
    }
)

# Terms typical of credential-theft / financial-fraud lures.
SUSPICIOUS_TERMS: frozenset[str] = frozenset(
    {
        "verify your account",
        "verify your identity",
        "confirm your password",
        "update your payment",
        "update your billing",
        "unusual activity",
        "unauthorized",
        "click here",
        "log in",
        "login",
        "sign in",
        "reset your password",
        "account has been",
        "account was",
        "security alert",
        "wire transfer",
        "gift card",
        "bank account",
        "social security",
        "invoice attached",
        "payment failed",
        "tax refund",
        "you have won",
        "claim your",
    }
)

# Extensions that should essentially never arrive by email unsolicited.
RISKY_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".exe",
        ".scr",
        ".js",
        ".jse",
        ".vbs",
        ".vbe",
        ".jar",
        ".bat",
        ".cmd",
        ".com",
        ".pif",
        ".msi",
        ".ps1",
        ".hta",
        ".wsf",
        ".lnk",
        ".iso",
        ".img",
    }
)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_html(html: str) -> str:
    """Crude tag strip to recover visible text for language features."""
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", html)).strip()


def shannon_entropy(text: str) -> float:
    """Shannon entropy (bits/char). High values flag random-looking domains."""
    if not text:
        return 0.0
    counts: dict[str, int] = {}
    for ch in text:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(text)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())
