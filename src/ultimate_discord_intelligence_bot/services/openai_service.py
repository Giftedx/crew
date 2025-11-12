"""Base OpenAI service with common functionality."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from openai import AsyncOpenAI


try:
    import jsonschema

    HAS_JSONSCHEMA = True
except ImportError:
    jsonschema = None
    HAS_JSONSCHEMA = False
from app.config.settings import Settings
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class OpenAIService:
    """Base OpenAI service with common functionality."""

    def __init__(self):
        """Initialize OpenAI service with configuration."""
        self.settings = Settings()
        self.client = AsyncOpenAI(
            api_key=self.settings.base_config.openai_api_key, base_url=self.settings.base_config.openai_base_url
        )
        self.max_retries = 3
        self.retry_delay = 1.0

    async def _make_request_with_retry(self, request_func, *args, **kwargs) -> StepResult:
        """Make OpenAI request with exponential backoff retry."""
        for attempt in range(self.max_retries):
            try:
                result = await request_func(*args, **kwargs)
                return StepResult.ok(data=result)
            except Exception as e:
                logger.warning(f"OpenAI request attempt {attempt + 1} failed: {e!s}")
                if attempt == self.max_retries - 1:
                    return StepResult.fail(f"OpenAI request failed after {self.max_retries} attempts: {e!s}")
                await asyncio.sleep(self.retry_delay * 2**attempt)
        return StepResult.fail("Unexpected error in retry logic")

    async def _validate_response(self, response: Any, schema: dict | None = None) -> StepResult:
        """Validate OpenAI response against schema."""
        if not response:
            return StepResult.fail("Empty response from OpenAI")
        if schema:
            try:
                if HAS_JSONSCHEMA:
                    import jsonschema as js

                    js.validate(response, schema)
                else:
                    logger.warning("jsonschema not available, skipping validation")
            except Exception as e:
                return StepResult.fail(f"Response validation failed: {e!s}")
        return StepResult.ok(data=response)

    def _is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled via feature flags."""
        return getattr(self.settings.feature_flags, feature_name, False)

    async def _fallback_to_openrouter(self, fallback_func, *args, **kwargs) -> StepResult:
        """Fallback to OpenRouter service if OpenAI fails."""
        if not self._is_feature_enabled("ENABLE_OPENAI_FALLBACK"):
            return StepResult.fail("OpenAI fallback disabled")
        try:
            from platform.llm.providers.openrouter import OpenRouterService

            openrouter_service = OpenRouterService()
            return await fallback_func(openrouter_service, *args, **kwargs)
        except Exception as e:
            return StepResult.fail(f"OpenRouter fallback failed: {e!s}")

    def _get_model_config(self, model: str) -> dict[str, Any]:
        """Get model configuration with appropriate settings."""
        return {
            "model": model,
            "max_tokens": self.settings.base_config.openai_max_tokens,
            "temperature": self.settings.base_config.openai_temperature,
        }
