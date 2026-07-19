"""The rule set.

Each rule is a small pure function: given the features (and the parsed email for
context), it either fires — returning an Indicator with a point weight and a
plain-English explanation — or returns None. The scorer sums the points.

Weights are deliberately hand-tuned and visible here rather than hidden in a
model, because this layer's whole job is to be *explainable*. The ML model (M3)
provides the learned, probabilistic view that complements these rules; per the
project's core principle, neither the rules nor the LLM's later narrative is the
sole decider.
"""

from __future__ import annotations

from collections.abc import Callable

from app.schemas.email import ParsedEmail
from app.schemas.features import FeatureVector, Indicator, Severity

Rule = Callable[[FeatureVector, ParsedEmail], Indicator | None]


def _link_mismatch(f: FeatureVector, _p: ParsedEmail) -> Indicator | None:
    if f.link_mismatch_count <= 0:
        return None
    return Indicator(
        id="link_mismatch",
        title="Deceptive link text",
        category="url",
        severity=Severity.high,
        points=22,
        detail=(
            f"{f.link_mismatch_count} link(s) display one domain but actually point to "
            "another — a hallmark of credential-phishing."
        ),
    )


def _ip_url(f: FeatureVector, _p: ParsedEmail) -> Indicator | None:
    if f.ip_url_count <= 0:
        return None
    return Indicator(
        id="ip_url",
        title="Link to a raw IP address",
        category="url",
        severity=Severity.high,
        points=16,
        detail=(
            f"{f.ip_url_count} link(s) use a bare IP address instead of a domain name, "
            "bypassing domain reputation."
        ),
    )


def _spf_fail(f: FeatureVector, _p: ParsedEmail) -> Indicator | None:
    if not f.spf_fail:
        return None
    return Indicator(
        id="spf_fail",
        title="SPF authentication failed",
        category="auth",
        severity=Severity.high,
        points=14,
        detail="The sending server is not authorised to send for the From domain (SPF fail).",
    )


def _dmarc_fail(f: FeatureVector, _p: ParsedEmail) -> Indicator | None:
    if not f.dmarc_fail:
        return None
    return Indicator(
        id="dmarc_fail",
        title="DMARC authentication failed",
        category="auth",
        severity=Severity.high,
        points=14,
        detail="The message failed DMARC alignment — the From domain likely does not vouch for it.",
    )


def _dkim_missing(f: FeatureVector, _p: ParsedEmail) -> Indicator | None:
    if not f.dkim_missing:
        return None
    return Indicator(
        id="dkim_missing",
        title="No valid DKIM signature",
        category="auth",
        severity=Severity.low,
        points=6,
        detail="The message is not DKIM-signed by the sending domain; its contents are unverified.",
    )


def _reply_to_mismatch(f: FeatureVector, p: ParsedEmail) -> Indicator | None:
    if not f.reply_to_mismatch:
        return None
    from_domain = p.from_address.domain if p.from_address else "?"
    reply_domain = p.reply_to.domain if p.reply_to else "?"
    return Indicator(
        id="reply_to_mismatch",
        title="Reply-To domain differs from sender",
        category="sender",
        severity=Severity.medium,
        points=12,
        detail=f"Replies would go to '{reply_domain}', not the sender's domain '{from_domain}'.",
    )


def _risky_attachment(f: FeatureVector, p: ParsedEmail) -> Indicator | None:
    if f.risky_attachment_count <= 0:
        return None
    names = ", ".join(a.filename for a in p.attachments if a.filename) or "attachment"
    return Indicator(
        id="risky_attachment",
        title="Dangerous attachment type",
        category="attachment",
        severity=Severity.critical,
        points=20,
        detail=f"Executable/script attachment(s) present ({names}) — high malware risk.",
    )


def _suspicious_keywords(f: FeatureVector, _p: ParsedEmail) -> Indicator | None:
    if f.suspicious_keyword_count < 1:
        return None
    points = min(f.suspicious_keyword_count * 4, 16)
    severity = Severity.medium if f.suspicious_keyword_count >= 2 else Severity.low
    return Indicator(
        id="suspicious_keywords",
        title="Phishing-style language",
        category="content",
        severity=severity,
        points=points,
        detail=f"{f.suspicious_keyword_count} known lure phrase(s) detected (credential/payment).",
    )


def _urgency(f: FeatureVector, _p: ParsedEmail) -> Indicator | None:
    if f.urgency_score <= 0:
        return None
    return Indicator(
        id="urgency",
        title="Manufactured urgency",
        category="content",
        severity=Severity.medium if f.urgency_score >= 0.66 else Severity.low,
        points=round(f.urgency_score * 12),
        detail="The message pressures the reader to act immediately — a social-engineering tactic.",
    )


def _shouting(f: FeatureVector, _p: ParsedEmail) -> Indicator | None:
    if f.capital_ratio <= 0.30 or f.body_length <= 20:
        return None
    return Indicator(
        id="shouting_caps",
        title="Excessive capitalisation",
        category="content",
        severity=Severity.low,
        points=6,
        detail=f"{round(f.capital_ratio * 100)}% of letters are uppercase — a scare tactic.",
    )


def _high_entropy_domain(f: FeatureVector, _p: ParsedEmail) -> Indicator | None:
    if f.max_domain_entropy <= 3.5:
        return None
    return Indicator(
        id="high_entropy_domain",
        title="Random-looking link domain",
        category="url",
        severity=Severity.medium,
        points=8,
        detail=(
            f"A link domain has high character entropy ({f.max_domain_entropy}), consistent with "
            "algorithmically-generated (throwaway) domains."
        ),
    )


def _many_urls(f: FeatureVector, _p: ParsedEmail) -> Indicator | None:
    if f.url_count <= 10:
        return None
    return Indicator(
        id="many_urls",
        title="Unusually many links",
        category="url",
        severity=Severity.low,
        points=5,
        detail=f"The message contains {f.url_count} links.",
    )


# Order here is only cosmetic; the scorer sorts the fired indicators by points.
RULES: tuple[Rule, ...] = (
    _link_mismatch,
    _ip_url,
    _risky_attachment,
    _spf_fail,
    _dmarc_fail,
    _dkim_missing,
    _reply_to_mismatch,
    _suspicious_keywords,
    _urgency,
    _high_entropy_domain,
    _shouting,
    _many_urls,
)
