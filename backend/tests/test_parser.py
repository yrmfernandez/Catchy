"""Unit tests for the email parser, driven by real .eml fixtures."""

from pathlib import Path

import pytest

from app.services.parsing import EmailParserService

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def parser() -> EmailParserService:
    return EmailParserService()


def _load(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


# ---- Benign message --------------------------------------------------------


def test_benign_headers_and_auth(parser: EmailParserService) -> None:
    result = parser.parse(_load("benign.eml"))

    assert result.subject == "Your weekly Acme digest"
    assert result.from_address is not None
    assert result.from_address.domain == "acme.com"
    assert result.reply_to is not None
    assert result.reply_to.domain == "acme.com"
    assert result.reply_to_mismatch is False

    assert result.auth.spf == "pass"
    assert result.auth.dkim == "pass"
    assert result.auth.dmarc == "pass"
    assert result.auth.dkim_signature_present is True
    assert result.received_count == 1


def test_benign_bodies_and_urls(parser: EmailParserService) -> None:
    result = parser.parse(_load("benign.eml"))

    assert result.has_plain is True
    assert result.has_html is True
    assert result.attachments == []

    domains = {u.domain for u in result.urls}
    assert "www.acme.com" in domains
    assert all(u.anchor_mismatch is False for u in result.urls)
    assert all(u.is_ip is False for u in result.urls)


# ---- Phishing message ------------------------------------------------------


def test_phishing_spoofing_signals(parser: EmailParserService) -> None:
    result = parser.parse(_load("phishing.eml"))

    assert result.from_address.domain == "paypa1-secure.com"
    assert result.reply_to.domain == "mailbox-verify.ru"
    assert result.reply_to_mismatch is True

    assert result.auth.spf == "fail"
    assert result.auth.dkim == "none"
    assert result.auth.dmarc == "fail"
    assert result.auth.dkim_signature_present is False


def test_phishing_link_mismatch_and_ip(parser: EmailParserService) -> None:
    result = parser.parse(_load("phishing.eml"))

    # The visible text says paypal.com but the href points at a raw IP.
    mismatched = [u for u in result.urls if u.anchor_mismatch]
    assert len(mismatched) == 1
    assert mismatched[0].is_ip is True
    assert mismatched[0].anchor_text == "https://www.paypal.com/login"

    assert any(u.is_ip for u in result.urls)


def test_phishing_attachment_metadata_only(parser: EmailParserService) -> None:
    result = parser.parse(_load("phishing.eml"))

    assert len(result.attachments) == 1
    att = result.attachments[0]
    assert att.filename == "invoice.pdf.exe"
    assert att.extension == ".exe"
    assert att.content_type == "application/octet-stream"
    assert att.size_bytes > 0
    assert att.sha256 and len(att.sha256) == 64


# ---- Robustness ------------------------------------------------------------


def test_garbage_input_does_not_raise(parser: EmailParserService) -> None:
    # Parsing must be total: hostile/garbage input yields a best-effort result.
    result = parser.parse("this is not a valid email at all \x00\xff")
    assert result.attachments == []
    assert result.auth.spf is None


def test_accepts_str_and_bytes(parser: EmailParserService) -> None:
    raw = _load("benign.eml")
    from_bytes = parser.parse(raw)
    from_str = parser.parse(raw.decode("utf-8"))
    assert from_bytes.subject == from_str.subject
