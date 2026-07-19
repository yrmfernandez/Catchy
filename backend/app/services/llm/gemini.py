"""Gemini provider via the REST API.

We call the generativelanguage REST endpoint directly with httpx rather than
pulling in the google-generativeai SDK — one less heavy dependency, and the call
is trivial. `responseMimeType: application/json` asks Gemini to return strict JSON,
and the system instruction is sent separately from the (untrusted) user content.
"""

from __future__ import annotations

import httpx

from app.services.llm.base import LlmError, LlmProvider

_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiProvider(LlmProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout: float) -> None:
        self._key = api_key
        self.model = model
        self._timeout = timeout

    async def complete(self, system: str, user: str) -> str:
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
                "maxOutputTokens": 800,
            },
        }
        url = _ENDPOINT.format(model=self.model)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, params={"key": self._key}, json=payload)
        except httpx.HTTPError as exc:
            raise LlmError(f"Gemini transport error: {exc}") from exc

        if resp.status_code != 200:
            raise LlmError(f"Gemini HTTP {resp.status_code}: {resp.text[:200]}")

        try:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, ValueError) as exc:
            raise LlmError(f"Gemini malformed response: {exc}") from exc
