"""LLM provider abstraction for the agent orchestrator.

Provides a protocol for LLM generation with two implementations:
- OpenAILLMProvider: wraps openai.AsyncOpenAI for production use
- MockLLMProvider: returns deterministic strings for testing

This abstraction allows all tests to run without API keys.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract protocol for LLM generation."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The user/system prompt to send.
            system_prompt: The system prompt for context.

        Returns:
            The LLM's text response.
        """

    @abstractmethod
    async def classify(self, prompt: str, system_prompt: str) -> str:
        """Generate a classification response.

        Used for intent classification where the response should be
        a single intent string.

        Args:
            prompt: The user message to classify.
            system_prompt: Classification instructions.

        Returns:
            The classified intent string.
        """


class OpenAILLMProvider(LLMProvider):
    """Production LLM provider using OpenAI-compatible API."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.model = model or settings.openai_model
        self._api_key = api_key or settings.openai_api_key
        self._base_url = base_url or (settings.openai_base_url or None)
        self._client: Any | None = None

    def _get_client(self) -> Any:
        """Lazy-initialize the OpenAI client."""
        if self._client is None:
            from openai import AsyncOpenAI

            kwargs: dict[str, Any] = {"api_key": self._api_key, "timeout": 120.0}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    async def generate(self, prompt: str, system_prompt: str) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""

    async def classify(self, prompt: str, system_prompt: str) -> str:
        import asyncio
        client = self._get_client()
        try:
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                ),
                timeout=5.0,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as exc:
            logger.warning(f"LLM classify call failed or timed out ({exc})")
            raise


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing.

    Returns deterministic responses based on the prompt content.
    """

    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self._responses = responses or {}
        self.call_count = 0

    async def generate(self, prompt: str, system_prompt: str) -> str:
        self.call_count += 1
        # Check for exact match first
        for key, value in self._responses.items():
            if key in prompt:
                return value
        # Default response
        return f"Mock response to: {prompt[:100]}"

    async def classify(self, prompt: str, system_prompt: str) -> str:
        self.call_count += 1
        # Check for exact match first
        for key, value in self._responses.items():
            if key in prompt:
                return value
        # Default: classify as source_candidates if message mentions candidates/jobs
        lower = prompt.lower()
        if any(w in lower for w in ["find", "search", "candidate", "java", "python", "developer", "engineer", "role", "job", "match"]):
            return "source_candidates"
        if any(w in lower for w in ["pipeline", "status", "progress", "submitted", "interview"]):
            return "check_pipeline"
        if any(w in lower for w in ["remember", "preference", "always", "never", "only", "require", "rule"]):
            return "update_preferences"
        if any(w in lower for w in ["draft", "outreach", "email", "message", "contact", "reach out"]):
            return "draft_outreach"
        return "general_conversation"

    def reset(self) -> None:
        """Reset call count."""
        self.call_count = 0


# Module-level factory for easy import
def get_llm_provider(use_mock: bool = False) -> LLMProvider:
    """Get an LLM provider instance.

    Args:
        use_mock: If True, return MockLLMProvider. Otherwise, OpenAILLMProvider.

    Returns:
        An LLMProvider instance.
    """
    if use_mock:
        return MockLLMProvider()
    return OpenAILLMProvider()
