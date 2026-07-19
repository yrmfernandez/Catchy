"""Dataset loading.

Two sources:
  * a CSV with columns `raw_email,label` (label 1=phish, 0=legit) — this is where
    real public corpora plug in (Nazario phishing, Enron/SpamAssassin ham, Kaggle
    phishing-email sets). See ml/README.md for links and the expected format.
  * a seeded synthetic generator — so `train.py` and the test suite run with zero
    external downloads and are fully reproducible. It fabricates labelled raw
    RFC-822 messages exercising the real signals (spoofing, link mismatch, IP
    links, urgency, dangerous attachments) with enough noise to be non-trivial.

The synthetic set is a stand-in for demoing the pipeline end-to-end, not a claim
of real-world accuracy — swap in public data before quoting metrics.
"""

from __future__ import annotations

import csv
import random
from email.message import EmailMessage
from pathlib import Path

Sample = tuple[str, int]

# -- vocab -------------------------------------------------------------------

_LEGIT_BRANDS = [
    ("Acme", "acme.com"),
    ("GitHub", "github.com"),
    ("Notion", "notion.so"),
    ("Spotify", "spotify.com"),
    ("Dropbox", "dropbox.com"),
    ("Slack", "slack.com"),
    ("Figma", "figma.com"),
]
_LEGIT_SUBJECTS = [
    "Your weekly digest",
    "Receipt for your recent order",
    "Welcome aboard",
    "Your monthly statement is ready",
    "A new comment on your project",
    "Meeting notes from today",
    "Your invoice is available",
]
_LEGIT_SENTENCES = [
    "Thanks for being with us this month.",
    "Here is a summary of your recent activity.",
    "You can review the details in your dashboard.",
    "We appreciate your continued support.",
    "Let us know if you have any questions.",
    "Your team shared a few updates this week.",
    "No action is needed on your part.",
]

_SPOOF_TARGETS = [
    ("PayPal", "paypal.com", "paypa1-secure.com"),
    ("Apple", "apple.com", "apple-id-verify.com"),
    ("Microsoft", "microsoft.com", "micros0ft-support.com"),
    ("Amazon", "amazon.com", "amazon-billing-alert.ru"),
    ("Netflix", "netflix.com", "netflix-account-update.top"),
    ("DHL", "dhl.com", "dhl-delivery-confirm.info"),
]
_REPLY_TO_DOMAINS = ["mailbox-verify.ru", "recovery-team.top", "secure-inbox.info", "no-reply.zzz"]
_PHISH_SUBJECTS = [
    "Urgent: your account has been limited",
    "Action required: verify your identity immediately",
    "Your payment failed - update your billing now",
    "Security alert: unusual sign-in detected",
    "Final notice: your account will be suspended",
    "You have won a reward - claim it now",
]
_PHISH_SENTENCES = [
    "We detected unusual activity on your account.",
    "Your account has been temporarily suspended.",
    "Please verify your identity to avoid suspension.",
    "Confirm your password within 24 hours or lose access.",
    "Click here to restore your account immediately.",
    "Update your payment details to continue service.",
    "This is your final warning before we close the account.",
]
_RISKY_ATTACHMENTS = ["invoice.pdf.exe", "document.js", "payment_details.scr", "receipt.zip.exe"]


def _msg_common(m: EmailMessage, sender_name: str, sender_addr: str, subject: str) -> None:
    m["From"] = f"{sender_name} <{sender_addr}>"
    m["To"] = "user@example.org"
    m["Subject"] = subject
    m["Date"] = "Mon, 14 Jul 2026 09:00:00 +0000"
    m["Message-ID"] = f"<{random.randint(1000, 9999)}@{sender_addr.split('@')[-1]}>"


# "Hard" cases create class overlap so the model isn't handed a trivially
# separable problem: legit mail that happens to sound urgent, and stealthy phish
# sent from a compromised (SPF-passing) account. Realistic corpora are full of
# both, and they are exactly where the ML layer earns its keep over the rules.
_HARD_LEGIT_SUBJECTS = [
    "Action needed: confirm your email address",
    "Your subscription expires soon",
    "Please review your recent sign-in",
]
_HARD_LEGIT_SENTENCE = "Please verify your account details to keep your subscription active."


def _make_legit(rng: random.Random, hard: bool = False, ambiguous: bool = False) -> str:
    name, domain = rng.choice(_LEGIT_BRANDS)
    subject = rng.choice(_HARD_LEGIT_SUBJECTS if (hard or ambiguous) else _LEGIT_SUBJECTS)
    if ambiguous:
        # Legit mail that genuinely sounds phishy — the model must not overreact.
        body_sentences = rng.sample(_PHISH_SENTENCES, k=2) + rng.sample(_LEGIT_SENTENCES, k=1)
    else:
        body_sentences = rng.sample(_LEGIT_SENTENCES, k=rng.randint(2, 4))
        if hard:
            body_sentences.append(_HARD_LEGIT_SENTENCE)
    body = " ".join(body_sentences)
    link = f"https://www.{domain}/account"

    m = EmailMessage()
    _msg_common(m, name, f"news@{domain}", subject)
    m["Reply-To"] = f"{name} <support@{domain}>"
    m["Authentication-Results"] = (
        f"mx.example.org; spf=pass smtp.mailfrom={domain}; "
        f"dkim=pass header.d={domain}; dmarc=pass header.from={domain}"
    )
    m["DKIM-Signature"] = f"v=1; a=rsa-sha256; d={domain}; s=sel; b=abc"
    m["Received"] = (
        f"from mail.{domain} (mail.{domain} [203.0.113.5]) by mx.example.org; "
        "Mon, 14 Jul 2026 09:00:00 +0000"
    )
    m.set_content(f"{body}\nVisit {link} for details.")
    m.add_alternative(
        f"<html><body><p>{body}</p><p><a href='{link}'>Open dashboard</a></p></body></html>",
        subtype="html",
    )
    # A little noise: some legit mail carries a benign PDF.
    if rng.random() < 0.15:
        m.add_attachment(
            b"%PDF-1.4 fake", maintype="application", subtype="pdf", filename="statement.pdf"
        )
    return m.as_string()


def _make_phish(rng: random.Random, hard: bool = False, ambiguous: bool = False) -> str:
    brand, real_domain, spoof_domain = rng.choice(_SPOOF_TARGETS)
    subject = rng.choice(_PHISH_SUBJECTS)
    if ambiguous:
        # Phish written in bland, legit-sounding language — a hard positive.
        body = " ".join(rng.sample(_LEGIT_SENTENCES, k=2) + rng.sample(_PHISH_SENTENCES, k=1))
    else:
        body = " ".join(rng.sample(_PHISH_SENTENCES, k=rng.randint(2, 4)))

    # Ambiguous phish are also structurally stealthy (like hard).
    hard = hard or ambiguous

    if hard:
        # No structural tell: the link points honestly at the look-alike domain,
        # no mismatch, no IP. Only the wording + suspicious sender give it away.
        href = f"https://www.{spoof_domain}/login"
        shown = href
    else:
        # An IP link or a throwaway domain, shown under a real-brand URL (mismatch).
        if rng.random() < 0.5:
            bad_host = f"198.51.100.{rng.randint(2, 250)}"
        else:
            bad_host = f"{''.join(rng.choices('abcdefghjkmnpqrstuvwxyz0123456789', k=10))}.top"
        href = f"http://{bad_host}/login"
        shown = f"https://www.{real_domain}/login"

    m = EmailMessage()
    _msg_common(m, f"{brand} Service", f"service@{spoof_domain}", subject)

    if hard:
        # Stealthy: compromised account passes SPF/DKIM, no attachment, Reply-To
        # aligned. The lure language and the mismatched link are the only tells.
        m["Reply-To"] = f"{brand} Service <service@{spoof_domain}>"
        m["Authentication-Results"] = (
            f"mx.example.org; spf=pass smtp.mailfrom={spoof_domain}; "
            f"dkim=pass header.d={spoof_domain}; dmarc=pass header.from={spoof_domain}"
        )
        m["DKIM-Signature"] = f"v=1; a=rsa-sha256; d={spoof_domain}; s=sel; b=abc"
    else:
        m["Reply-To"] = f"<recover@{rng.choice(_REPLY_TO_DOMAINS)}>"
        spf = rng.choice(["fail", "fail", "softfail", "none"])
        m["Authentication-Results"] = (
            f"mx.example.org; spf={spf} smtp.mailfrom={spoof_domain}; dkim=none; "
            f"dmarc=fail header.from={spoof_domain}"
        )
    m["Received"] = (
        "from unknown (unknown [45.9.148.3]) by mx.example.org; Tue, 15 Jul 2026 03:12:00 +0000"
    )
    m.set_content(f"{body}\nVerify now: {href}")
    m.add_alternative(
        f"<html><body><p>{body}</p><p><a href='{href}'>{shown}</a></p></body></html>",
        subtype="html",
    )
    if not hard and rng.random() < 0.4:
        m.add_attachment(
            b"MZ fake-exe",
            maintype="application",
            subtype="octet-stream",
            filename=rng.choice(_RISKY_ATTACHMENTS),
        )
    return m.as_string()


def generate(n: int = 500, seed: int = 42) -> list[Sample]:
    """Balanced synthetic dataset of (raw_email, label)."""
    rng = random.Random(seed)
    samples: list[Sample] = []
    for i in range(n):
        roll = rng.random()
        ambiguous = roll < 0.12  # ~12% genuinely overlapping cases
        hard = not ambiguous and roll < 0.32  # ~20% structurally-stealthy cases
        if i % 2 == 0:
            samples.append((_make_legit(rng, hard=hard, ambiguous=ambiguous), 0))
        else:
            samples.append((_make_phish(rng, hard=hard, ambiguous=ambiguous), 1))
    rng.shuffle(samples)
    return samples


def load_csv(path: Path) -> list[Sample]:
    """Load a `raw_email,label` CSV (real public data plugs in here)."""
    out: list[Sample] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            out.append((row["raw_email"], int(row["label"])))
    return out


def load_dataset(csv_path: Path | None = None, *, n_synthetic: int = 500) -> list[Sample]:
    """Prefer a real CSV if present; otherwise fall back to synthetic data."""
    if csv_path and csv_path.exists():
        return load_csv(csv_path)
    return generate(n=n_synthetic)
