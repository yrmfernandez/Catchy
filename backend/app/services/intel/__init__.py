"""Threat-intelligence subpackage.

Asks external reputation sources about an email's URLs, domains, attachments, and
sender, and normalizes the answers into a ThreatIntel result. Everything here is
optional and best-effort: disabled by default, cached in Redis, bounded by
per-call timeouts, and safe to fail — a dead provider or missing key never breaks
a scan.
"""

from app.services.intel.service import ThreatIntelService

__all__ = ["ThreatIntelService"]
