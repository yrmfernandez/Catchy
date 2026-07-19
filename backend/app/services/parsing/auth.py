"""SPF / DKIM / DMARC extraction.

We do not *verify* authentication here — verification requires live DNS lookups
and the original SMTP session, which the receiving mail server already did. Its
verdict is recorded in the `Authentication-Results` header (RFC 8601). We read
that verdict, plus the cheaper `Received-SPF` header and the presence of a
`DKIM-Signature`. Absent or failing results are meaningful phishing signals.
"""

from __future__ import annotations

import re
from email.message import EmailMessage

from app.schemas.email import AuthResults

# `spf=pass`, `dkim = fail`, `dmarc=none (p=reject ...)` -> capture the token.
_METHOD_RE = {
    "spf": re.compile(r"\bspf\s*=\s*(\w+)", re.IGNORECASE),
    "dkim": re.compile(r"\bdkim\s*=\s*(\w+)", re.IGNORECASE),
    "dmarc": re.compile(r"\bdmarc\s*=\s*(\w+)", re.IGNORECASE),
}
# `Received-SPF: Pass (google.com: domain of ...)` -> leading verdict word.
_RECEIVED_SPF_RE = re.compile(r"^\s*(\w+)", re.IGNORECASE)


def extract_auth(msg: EmailMessage) -> AuthResults:
    # There can be several Authentication-Results headers (one per hop). Join them
    # so a verdict in any hop is visible to the regexes.
    ar_values = msg.get_all("Authentication-Results") or []
    ar_blob = " ; ".join(str(v) for v in ar_values)

    results: dict[str, str | None] = {"spf": None, "dkim": None, "dmarc": None}
    for method, pattern in _METHOD_RE.items():
        m = pattern.search(ar_blob)
        if m:
            results[method] = m.group(1).lower()

    # Fall back to Received-SPF for the SPF verdict if not already found.
    if results["spf"] is None:
        received_spf = msg.get("Received-SPF")
        if received_spf:
            m = _RECEIVED_SPF_RE.match(str(received_spf))
            if m:
                results["spf"] = m.group(1).lower()

    return AuthResults(
        spf=results["spf"],
        dkim=results["dkim"],
        dmarc=results["dmarc"],
        dkim_signature_present=msg.get("DKIM-Signature") is not None,
        raw=ar_blob or None,
    )
