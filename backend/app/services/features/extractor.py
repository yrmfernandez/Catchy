"""FeatureExtractor: derive the numeric FeatureVector from a ParsedEmail.

Deterministic and side-effect free. This is the single source of truth for
feature computation — M3's training pipeline imports *this* class so the numbers
a model learns from are byte-for-byte the numbers it sees in production.
"""

from __future__ import annotations

from app.schemas.email import ParsedEmail
from app.schemas.features import FeatureVector
from app.services.features.lexicons import (
    RISKY_EXTENSIONS,
    SUSPICIOUS_TERMS,
    URGENCY_TERMS,
    shannon_entropy,
    strip_html,
)

# Number of urgency cues at which urgency_score saturates to 1.0.
_URGENCY_SATURATION = 3


class FeatureExtractor:
    """Stateless; share one instance."""

    def extract(self, parsed: ParsedEmail) -> FeatureVector:
        visible_text = self._visible_text(parsed)
        lang_text = f"{parsed.subject or ''}\n{visible_text}"
        lowered = lang_text.lower()

        return FeatureVector(
            # URLs / links
            url_count=len(parsed.urls),
            unique_domain_count=len({u.domain for u in parsed.urls if u.domain}),
            ip_url_count=sum(1 for u in parsed.urls if u.is_ip),
            link_mismatch_count=sum(1 for u in parsed.urls if u.anchor_mismatch),
            max_domain_entropy=self._max_domain_entropy(parsed),
            # Authentication
            spf_fail=parsed.auth.spf in {"fail", "softfail"},
            dkim_missing=(
                parsed.auth.dkim != "pass" and not parsed.auth.dkim_signature_present
            ),
            dmarc_fail=parsed.auth.dmarc == "fail",
            reply_to_mismatch=parsed.reply_to_mismatch,
            # Attachments
            attachment_count=len(parsed.attachments),
            risky_attachment_count=sum(
                1 for a in parsed.attachments if (a.extension or "") in RISKY_EXTENSIONS
            ),
            # Content / language
            suspicious_keyword_count=sum(1 for t in SUSPICIOUS_TERMS if t in lowered),
            urgency_score=self._urgency_score(lowered),
            capital_ratio=self._capital_ratio(lang_text),
            exclamation_count=lang_text.count("!"),
            html_ratio=self._html_ratio(parsed),
            body_length=len(visible_text),
        )

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _visible_text(parsed: ParsedEmail) -> str:
        if parsed.body_plain:
            return parsed.body_plain
        if parsed.body_html:
            return strip_html(parsed.body_html)
        return ""

    @staticmethod
    def _urgency_score(lowered: str) -> float:
        hits = sum(1 for t in URGENCY_TERMS if t in lowered)
        return min(hits / _URGENCY_SATURATION, 1.0)

    @staticmethod
    def _capital_ratio(text: str) -> float:
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 0.0
        return sum(1 for c in letters if c.isupper()) / len(letters)

    @staticmethod
    def _html_ratio(parsed: ParsedEmail) -> float:
        html_len = len(parsed.body_html or "")
        text_len = len(parsed.body_plain or "")
        total = html_len + text_len
        return html_len / total if total else 0.0

    @staticmethod
    def _max_domain_entropy(parsed: ParsedEmail) -> float:
        best = 0.0
        for url in parsed.urls:
            if not url.domain or url.is_ip:
                continue
            parts = url.domain.split(".")
            core = parts[-2] if len(parts) >= 2 else url.domain
            best = max(best, shannon_entropy(core))
        return round(best, 3)
