"""LLM analyst subpackage: explain a ScanResult (Gemini-first, swappable)."""

from __future__ import annotations

from app.core.config import Settings
from app.services.llm.analyst import LlmAnalyst
from app.services.llm.base import LlmProvider
from app.services.llm.gemini import GeminiProvider


def build_provider(settings: Settings) -> LlmProvider | None:
    """Select a provider from config, or None (=> analyst unavailable)."""
    if not settings.llm_enabled:
        return None
    if settings.llm_provider == "gemini" and settings.gemini_api_key:
        return GeminiProvider(
            settings.gemini_api_key, settings.llm_model, settings.llm_timeout_seconds
        )
    return None


__all__ = ["LlmAnalyst", "LlmProvider", "GeminiProvider", "build_provider"]
