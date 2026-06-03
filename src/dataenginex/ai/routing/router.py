"""Multi-model router — routes tasks to providers based on complexity."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from the LLM."""


class ModelRouter:
    """Routes tasks to the best LLM provider based on complexity.

    Complexity levels:
        - "simple"   → local provider (e.g. Ollama)
        - "moderate" → mid-tier provider (e.g. OpenAI)
        - "complex"  → top-tier provider (e.g. Anthropic)
    """

    COMPLEXITY_ORDER: list[str] = ["simple", "moderate", "complex"]

    DEFAULT_MAPPING: dict[str, str] = {
        "simple": "ollama",
        "moderate": "openai",
        "complex": "anthropic",
    }

    def __init__(
        self,
        providers: dict[str, BaseProvider],
        mapping: dict[str, str] | None = None,
    ) -> None:
        self._providers = providers
        self._mapping = mapping or self.DEFAULT_MAPPING

    def route(self, task: str, complexity: str = "moderate") -> BaseProvider:
        """Select a provider based on task complexity.

        Raises:
            ValueError: If complexity level is unknown.
            KeyError: If no provider is registered for the complexity level.
        """
        if complexity not in self._mapping:
            msg = f"Unknown complexity level: {complexity!r}"
            raise ValueError(msg)
        provider_key = self._mapping[complexity]
        if provider_key not in self._providers:
            msg = f"No provider registered for {provider_key!r}"
            raise KeyError(msg)
        return self._providers[provider_key]
