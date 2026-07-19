"""LlmAnalyst: turn a ScanResult into a human explanation.

Runs the configured provider against the hardened prompt, parses the JSON, and
returns an LlmAnalysis. Every failure mode (no provider, timeout, transport
error, unparseable output) degrades to `available=False` with a reason — the LLM
is the last and most optional layer, and must never break a scan.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re

from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.llm import LlmAnalysis, LlmAnalysisPayload
from app.schemas.scan import ScanResult
from app.services.llm.base import LlmProvider
from app.services.llm.prompt import build_system, build_user

logger = logging.getLogger("catchy.llm")

_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


class LlmAnalyst:
    def __init__(self, provider: LlmProvider | None, settings: Settings) -> None:
        self._provider = provider
        self._settings = settings

    @property
    def available(self) -> bool:
        return self._provider is not None

    async def analyze(self, result: ScanResult) -> LlmAnalysis:
        if self._provider is None:
            return LlmAnalysis.unavailable("no LLM provider configured")

        system = build_system()
        user = build_user(result, self._settings.llm_max_input_chars)
        try:
            raw = await asyncio.wait_for(
                self._provider.complete(system, user),
                timeout=self._settings.llm_timeout_seconds + 2,
            )
        except Exception as exc:  # noqa: BLE001 - any provider failure -> degrade
            logger.warning("LLM analysis failed: %s", exc)
            return LlmAnalysis.unavailable(f"{type(exc).__name__}: {exc}"[:200])

        payload = _parse(raw)
        if payload is None:
            return LlmAnalysis.unavailable("could not parse model output")

        return LlmAnalysis(
            available=True,
            provider=self._provider.name,
            model=self._provider.model,
            summary=payload.summary or None,
            why_suspicious=payload.why_suspicious,
            attack_techniques=payload.attack_techniques,
            recommendations=payload.recommendations,
            confidence=_clamp(payload.confidence),
        )


def _parse(raw: str) -> LlmAnalysisPayload | None:
    text = _FENCE_RE.sub("", raw.strip())
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    try:
        return LlmAnalysisPayload.model_validate(data)
    except ValidationError:
        return None


def _clamp(value: float | None) -> float | None:
    if value is None:
        return None
    return max(0.0, min(1.0, float(value)))
