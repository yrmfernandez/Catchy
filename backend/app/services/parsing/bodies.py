"""Body extraction: the plain-text and HTML parts of the message.

`get_body()` applies the stdlib's preference logic to find the "main" body, but
we want both representations when present (feature engineering compares the HTML-
to-text ratio), so we also walk the parts explicitly.
"""

from __future__ import annotations

from email.message import EmailMessage


def _decode(part: EmailMessage) -> str:
    try:
        content = part.get_content()
    except Exception:  # noqa: BLE001 - unknown charset etc.: best-effort decode
        raw = part.get_payload(decode=True) or b""
        return raw.decode("utf-8", "replace")
    return content if isinstance(content, str) else str(content)


def extract_bodies(msg: EmailMessage) -> tuple[str | None, str | None]:
    """Return (plain_text, html) — either may be None."""
    plain: str | None = None
    html: str | None = None

    if not msg.is_multipart():
        content = _decode(msg)
        if msg.get_content_type() == "text/html":
            return None, content
        return content, None

    for part in msg.walk():
        if not isinstance(part, EmailMessage) or part.is_multipart():
            continue
        # Skip anything that presents as an attachment.
        disposition = (part.get_content_disposition() or "").lower()
        if disposition == "attachment":
            continue
        ctype = part.get_content_type()
        if ctype == "text/plain" and plain is None:
            plain = _decode(part)
        elif ctype == "text/html" and html is None:
            html = _decode(part)

    return plain, html
