"""Attachment metadata extraction.

Security-critical rule: we look at attachments, we never keep them. For each
attachment we record filename, content type, size, extension, and a SHA-256 of
the decoded bytes (useful later for VirusTotal lookups by hash), then drop the
payload. Nothing executable is ever written to disk.
"""

from __future__ import annotations

import hashlib
from email.message import EmailMessage

from app.schemas.email import Attachment


def _extension(filename: str | None) -> str | None:
    if not filename or "." not in filename:
        return None
    return "." + filename.rsplit(".", 1)[1].lower()


def extract_attachments(msg: EmailMessage) -> list[Attachment]:
    out: list[Attachment] = []
    # iter_attachments() yields exactly the parts the stdlib considers attachments
    # (Content-Disposition: attachment, or inline parts with a filename), so we
    # don't misclassify the body as an attachment.
    for part in msg.iter_attachments():
        if not isinstance(part, EmailMessage):
            continue
        filename = part.get_filename()
        try:
            payload = part.get_content()
        except Exception:  # noqa: BLE001 - undecodable part: fall back to raw bytes
            payload = part.get_payload(decode=True) or b""
        data = payload if isinstance(payload, bytes) else str(payload).encode("utf-8", "replace")

        out.append(
            Attachment(
                filename=filename,
                content_type=part.get_content_type(),
                extension=_extension(filename),
                size_bytes=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
            )
        )
    return out
