"""Schemas describing a parsed email.

This is the structured object every downstream detection layer consumes: feature
engineering (M2), the ML model (M3/M4), and the LLM analyst (M6) all read from a
`ParsedEmail`. Keeping it an explicit, typed contract — rather than passing raw
`email.message.Message` objects around — is what lets those layers stay decoupled
from the messy details of MIME parsing.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# ---- Building blocks -------------------------------------------------------


class EmailAddress(BaseModel):
    """A parsed address, split so features can reason about the domain."""

    raw: str = Field(description="Original header value, e.g. 'Acme <no-reply@acme.com>'")
    name: str | None = Field(default=None, description="Display name, if present")
    address: str | None = Field(default=None, description="addr-spec, e.g. no-reply@acme.com")
    domain: str | None = Field(default=None, description="Lowercased domain of the address")


class AuthResults(BaseModel):
    """Email-authentication verdicts.

    Values are normalised to lowercase tokens ('pass', 'fail', 'softfail',
    'neutral', 'none', ...) or None when the signal is absent. A missing SPF/DKIM/
    DMARC result is itself a weak phishing signal, so None is meaningful, not just
    'unknown'.
    """

    spf: str | None = None
    dkim: str | None = None
    dmarc: str | None = None
    dkim_signature_present: bool = Field(
        default=False, description="A DKIM-Signature header exists (independent of verification)"
    )
    raw: str | None = Field(default=None, description="Raw Authentication-Results header, if any")


class ExtractedUrl(BaseModel):
    """A URL found in the body, with the signals that make it suspicious."""

    url: str
    scheme: str | None = None
    host: str | None = None
    domain: str | None = Field(
        default=None, description="Registrable-ish domain (host, lowercased)"
    )
    is_ip: bool = Field(default=False, description="Host is a literal IP address")
    in_html: bool = Field(default=False, description="Came from an HTML href/src attribute")
    anchor_text: str | None = Field(
        default=None, description="Visible text of the <a>, when the URL is a link target"
    )
    anchor_mismatch: bool = Field(
        default=False,
        description="Anchor text names a different domain than the href points to",
    )


class Attachment(BaseModel):
    """Attachment *metadata only* — the payload bytes are never retained."""

    filename: str | None = None
    content_type: str | None = None
    extension: str | None = None
    size_bytes: int = 0
    sha256: str | None = Field(default=None, description="Hash of the decoded payload")


# ---- Top-level result ------------------------------------------------------


class ParsedEmail(BaseModel):
    """The complete structured view of one email."""

    subject: str | None = None
    from_address: EmailAddress | None = Field(default=None, alias="from")
    reply_to: EmailAddress | None = None
    to: list[EmailAddress] = Field(default_factory=list)
    return_path: str | None = None
    date: str | None = None
    message_id: str | None = None

    auth: AuthResults = Field(default_factory=AuthResults)
    urls: list[ExtractedUrl] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)

    has_html: bool = False
    has_plain: bool = False
    body_plain: str | None = None
    body_html: str | None = None

    # Cheap structural counts, handy for feature engineering and quick display.
    header_count: int = 0
    received_count: int = Field(default=0, description="Number of Received hops")
    reply_to_mismatch: bool = Field(
        default=False, description="Reply-To domain differs from the From domain"
    )

    model_config = {"populate_by_name": True}
