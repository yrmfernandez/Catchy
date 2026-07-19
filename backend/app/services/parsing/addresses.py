"""Header and address extraction.

Uses the stdlib email library's structured header parsing (policy=default), which
correctly handles RFC 2047 encoded words ('=?utf-8?...?=') and folded headers so
we don't have to.
"""

from __future__ import annotations

from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import getaddresses

from app.schemas.email import EmailAddress


def _domain_of(addr_spec: str | None) -> str | None:
    if not addr_spec or "@" not in addr_spec:
        return None
    return addr_spec.rsplit("@", 1)[1].strip().lower() or None


def parse_address(raw: str | None) -> EmailAddress | None:
    """Parse a single-address header (From, Reply-To) into its parts."""
    if not raw:
        return None
    # getaddresses tolerates display names, comments, and angle brackets.
    parsed = getaddresses([raw])
    if not parsed:
        return EmailAddress(raw=raw)
    name, addr = parsed[0]
    return EmailAddress(
        raw=raw,
        name=name or None,
        address=addr.lower() or None,
        domain=_domain_of(addr),
    )


def parse_address_list(raw: str | None) -> list[EmailAddress]:
    """Parse a multi-address header (To, Cc) into a list."""
    if not raw:
        return []
    out: list[EmailAddress] = []
    for name, addr in getaddresses([raw]):
        if not name and not addr:
            continue
        out.append(
            EmailAddress(
                raw=str(Address(display_name=name or "", addr_spec=addr or "")) or addr,
                name=name or None,
                address=(addr.lower() or None),
                domain=_domain_of(addr),
            )
        )
    return out


def get_header(msg: EmailMessage, name: str) -> str | None:
    """Return a header as a plain, decoded string (or None)."""
    value = msg.get(name)
    if value is None:
        return None
    # str() on a structured header yields the decoded, unfolded form.
    return str(value).strip() or None
