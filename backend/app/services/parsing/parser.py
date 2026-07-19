"""EmailParserService: compose the pieces into a ParsedEmail.

This is the single entry point the API (and, later, the Celery scan task) calls.
It accepts raw bytes or str so it works for both an uploaded .eml file and a
pasted message. Parsing is total: a malformed message yields a best-effort
ParsedEmail rather than raising, because refusing to parse hostile input is its
own denial-of-service.
"""

from __future__ import annotations

from email import message_from_bytes, policy
from email.message import EmailMessage

from app.schemas.email import ParsedEmail
from app.services.parsing.addresses import get_header, parse_address, parse_address_list
from app.services.parsing.attachments import extract_attachments
from app.services.parsing.auth import extract_auth
from app.services.parsing.bodies import extract_bodies
from app.services.parsing.urls import extract_urls


class EmailParserService:
    """Stateless; safe to share as a singleton and inject as a dependency."""

    def parse(self, raw: bytes | str) -> ParsedEmail:
        if isinstance(raw, str):
            raw = raw.encode("utf-8", "replace")

        # policy=default gives us the modern EmailMessage API with decoded headers.
        msg = message_from_bytes(raw, policy=policy.default)
        if not isinstance(msg, EmailMessage):  # pragma: no cover - defensive
            msg = EmailMessage()

        from_addr = parse_address(get_header(msg, "From"))
        reply_to = parse_address(get_header(msg, "Reply-To"))
        plain, html = extract_bodies(msg)

        return ParsedEmail.model_validate(
            {
                "subject": get_header(msg, "Subject"),
                "from": from_addr,
                "reply_to": reply_to,
                "to": parse_address_list(get_header(msg, "To")),
                "return_path": get_header(msg, "Return-Path"),
                "date": get_header(msg, "Date"),
                "message_id": get_header(msg, "Message-ID"),
                "auth": extract_auth(msg),
                "urls": extract_urls(html=html, text=plain),
                "attachments": extract_attachments(msg),
                "has_html": html is not None,
                "has_plain": plain is not None,
                "body_plain": plain,
                "body_html": html,
                "header_count": len(msg.items()),
                "received_count": len(msg.get_all("Received") or []),
                "reply_to_mismatch": _reply_to_mismatch(from_addr, reply_to),
            }
        )


def _reply_to_mismatch(from_addr, reply_to) -> bool:
    if not from_addr or not reply_to or not from_addr.domain or not reply_to.domain:
        return False
    return from_addr.domain != reply_to.domain
