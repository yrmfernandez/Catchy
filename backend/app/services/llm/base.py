"""LLM provider contract.

Keeping providers behind this tiny interface is what makes the analyst
provider-swappable (Gemini today; OpenAI/Anthropic/local later) without touching
the prompt, parsing, or fusion code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class LlmError(Exception):
    """Raised for provider transport/response failures (caught by the analyst)."""


class LlmProvider(ABC):
    name: str
    model: str

    @abstractmethod
    async def complete(self, system: str, user: str) -> str:
        """Return the model's raw text response, or raise LlmError."""
