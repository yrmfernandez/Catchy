"""URL extraction and link-mismatch detection.

Two sources: anchors/`src` attributes in the HTML body, and bare URLs in the
plain-text body. For HTML links we also keep the visible anchor text, because a
link whose text *says* one domain while its href points at another is one of the
strongest phishing tells (the classic "www.paypal.com" -> attacker.example).
"""

from __future__ import annotations

import ipaddress
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

from app.schemas.email import ExtractedUrl

# Bare URLs in plain text. Deliberately conservative on the trailing char class
# so we don't swallow following punctuation.
_URL_RE = re.compile(r"\b(?:https?://|www\.)[^\s<>()\"'\]]+", re.IGNORECASE)
# A domain-looking token inside anchor text (for mismatch detection).
_DOMAIN_RE = re.compile(r"\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b", re.IGNORECASE)
# URL-bearing HTML attributes worth extracting.
_URL_ATTRS = {"href", "src"}


class _LinkCollector(HTMLParser):
    """Collect (href, anchor_text) links and standalone URL attributes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []  # (href, anchor_text)
        self.other_urls: list[str] = []
        self._href_stack: list[str] = []
        self._text_stack: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        adict = {k.lower(): (v or "") for k, v in attrs}
        if tag == "a":
            self._href_stack.append(adict.get("href", ""))
            self._text_stack.append([])
        for attr in _URL_ATTRS:
            if tag != "a" and attr in adict and adict[attr]:
                self.other_urls.append(adict[attr])
            elif tag == "a" and attr == "src" and adict.get("src"):
                self.other_urls.append(adict["src"])

    def handle_data(self, data: str) -> None:
        if self._text_stack:
            self._text_stack[-1].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href_stack:
            href = self._href_stack.pop()
            text = "".join(self._text_stack.pop()).strip()
            if href:
                self.links.append((href, text))


def _host_of(url: str) -> str | None:
    candidate = url if "://" in url else f"http://{url}"
    host = urlsplit(candidate).hostname
    return host.lower() if host else None


def _is_ip(host: str | None) -> bool:
    if not host:
        return False
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _hosts_related(a: str, b: str) -> bool:
    """True if two hosts share a registrable tail (subdomain-tolerant compare)."""
    a, b = a.lower(), b.lower()
    return a == b or a.endswith("." + b) or b.endswith("." + a)


def _anchor_mismatch(href_host: str | None, anchor_text: str) -> bool:
    if not href_host or not anchor_text:
        return False
    for token in _DOMAIN_RE.findall(anchor_text):
        # An anchor that literally spells out a domain different from where it
        # actually points is the mismatch we care about.
        if not _hosts_related(token.lower(), href_host):
            return True
    return False


def _build(url: str, *, in_html: bool, anchor_text: str | None) -> ExtractedUrl:
    host = _host_of(url)
    scheme = urlsplit(url).scheme.lower() or ("http" if url.lower().startswith("www.") else None)
    return ExtractedUrl(
        url=url,
        scheme=scheme,
        host=host,
        domain=host,
        is_ip=_is_ip(host),
        in_html=in_html,
        anchor_text=anchor_text or None,
        anchor_mismatch=_anchor_mismatch(host, anchor_text or ""),
    )


def extract_urls(*, html: str | None, text: str | None) -> list[ExtractedUrl]:
    out: list[ExtractedUrl] = []
    seen: set[str] = set()

    def add(u: ExtractedUrl) -> None:
        # Dedupe by URL. HTML is processed first, so a link that also appears as
        # bare text keeps its richer HTML form (anchor text + mismatch flag).
        if u.url not in seen:
            seen.add(u.url)
            out.append(u)

    if html:
        collector = _LinkCollector()
        try:
            collector.feed(html)
        except Exception:  # noqa: BLE001 - malformed HTML must never crash a scan
            pass
        for href, anchor in collector.links:
            if href.lower().startswith(("http://", "https://", "www.")):
                add(_build(href, in_html=True, anchor_text=anchor))
        for src in collector.other_urls:
            if src.lower().startswith(("http://", "https://", "www.")):
                add(_build(src, in_html=True, anchor_text=None))

    if text:
        for match in _URL_RE.findall(text):
            add(_build(match.rstrip(".,;:!?"), in_html=False, anchor_text=None))

    return out
