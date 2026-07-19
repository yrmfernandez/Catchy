"""Shared FastAPI dependencies.

Providers here are injected into routers with `Depends(...)`. Keeping construction
in one place is our dependency-injection seam: tests (and later milestones) can
override any provider without touching route code.
"""

from __future__ import annotations

from app.services.parsing import EmailParserService

# The parser is stateless, so a single shared instance is fine.
_email_parser = EmailParserService()


def get_email_parser() -> EmailParserService:
    return _email_parser
