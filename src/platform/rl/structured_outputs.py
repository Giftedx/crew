"""Instructor client factory for structured LLM outputs.

This module provides a factory for creating OpenAI clients wrapped with Instructor,
enabling automatic Pydantic validation, retry logic, and structured responses from LLMs.

Architecture:
- Wraps OpenAI/OpenRouter clients with instructor.from_openai()
- Handles retries automatically on validation failures
- Integrates with SecureConfig for settings
- Supports both sync and async client creation
- Respects ENABLE_INSTRUCTOR feature flag

Usage:
    from ai.structured_outputs import InstructorClientFactory
    from ai.response_models import FallacyAnalysisResult

    # Create an instructor-wrapped client
    client = InstructorClientFactory.create_client()

    # Make a structured LLM call
    result = client.chat.completions.create(
        model="gpt-4",
        response_model=FallacyAnalysisResult,
        messages=[{"role": "user", "content": "Analyze this argument..."}],
        max_retries=3
    )
    # result is now a validated FallacyAnalysisResult instance

Threading:
- Factory is thread-safe
- Clients are NOT reused (create per-request)
- For connection pooling, use OpenAI client's built-in pool
"""
from __future__ import annotations
import logging
from typing import Any, TypeVar
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel
from platform.config.configuration import get_config
try:
    import instructor
    from instructor import Instructor
    INSTRUCTOR_AVAILABLE = True
except ImportError:
    INSTRUCTOR_AVAILABLE = False
    instructor = None
    Instructor = Any
logger = logging.getLogger(__name__)
T = TypeVar('T', bound=BaseModel)

class InstructorClientFactory:
    """Factory for creating Instructor-wrapped OpenAI clients with validation and retry logic.

    This factory centralizes the creation of LLM clients that return structured,
    validated Pydantic models instead of raw text. It handles:
    - Feature flag checks (ENABLE_INSTRUCTOR)
    - Retry configuration from SecureConfig
    - Timeout settings
    - API key management
    - Graceful fallback when Instructor is disabled

    Methods:
        create_client: Create synchronous Instructor client
        create_async_client: Create asynchronous Instructor client
        is_enabled: Check if Instructor is enabled and available
    """

    @staticmethod
    def is_enabled() -> bool:
        """Check if Instructor is enabled via feature flag and library is available.

        Returns:
            True if ENABLE_INSTRUCTOR=True and instructor package is installed
        """
        config = get_config()
        if not INSTRUCTOR_AVAILABLE:
            if config.enable_instructor:
                logger.warning("ENABLE_INSTRUCTOR=True but 'instructor' package not installed. Install with: pip install instructor>=1.7.0")
            return False
        return config.enable_instructor

    @staticmethod
    def create_client(api_key: str | None=None, base_url: str | None=None, max_retries: int | None=None, timeout: int | None=None, **kwargs: Any) -> OpenAI | Instructor:
        """Create a synchronous OpenAI client, optionally wrapped with Instructor.

        If ENABLE_INSTRUCTOR=True, returns an Instructor-wrapped client that supports
        the `response_model` parameter for structured outputs. Otherwise, returns
        a standard OpenAI client.

        Args:
            api_key: OpenAI/OpenRouter API key. Defaults to OPENAI_API_KEY from config.
            base_url: Base URL for API. For OpenRouter, use https://openrouter.ai/api/v1
            max_retries: Maximum retry attempts on validation failures. Defaults to INSTRUCTOR_MAX_RETRIES.
            timeout: Request timeout in seconds. Defaults to INSTRUCTOR_TIMEOUT.
            **kwargs: Additional arguments passed to OpenAI client

        Returns:
            Instructor-wrapped client if enabled, otherwise standard OpenAI client

        Example:
            >>> from ai.structured_outputs import InstructorClientFactory
            >>> from ai.response_models import FallacyAnalysisResult
            >>>
            >>> # Using OpenRouter
            >>> client = InstructorClientFactory.create_client(
            ...     api_key=config.openrouter_api_key,
            ...     base_url="https://openrouter.ai/api/v1"
            ... )
            >>>
            >>> # Structured LLM call
            >>> result = client.chat.completions.create(
            ...     model="anthropic/claude-3.5-sonnet",
            ...     response_model=FallacyAnalysisResult,
            ...     messages=[{"role": "user", "content": "Analyze: All politicians are corrupt..."}]
            ... )
            >>> print(result.credibility_score)  # Validated float between 0-1
        """
        config = get_config()
        if api_key is None:
            api_key = config.openai_api_key
        if max_retries is None:
            max_retries = config.instructor_max_retries
        if timeout is None:
            timeout = config.instructor_timeout
        openai_client = OpenAI(api_key=api_key, base_url=base_url, max_retries=max_retries, timeout=timeout, **kwargs)
        if InstructorClientFactory.is_enabled():
            logger.debug(f'Creating Instructor client with max_retries={max_retries}, timeout={timeout}')
            return instructor.from_openai(openai_client)
        else:
            logger.debug('Instructor disabled, returning standard OpenAI client')
            return openai_client

    @staticmethod
    def create_async_client(api_key: str | None=None, base_url: str | None=None, max_retries: int | None=None, timeout: int | None=None, **kwargs: Any) -> AsyncOpenAI | Any:
        """Create an asynchronous OpenAI client, optionally wrapped with Instructor.

        Async variant of create_client(). Use this for async/await workflows.

        Args:
            api_key: OpenAI/OpenRouter API key. Defaults to OPENAI_API_KEY from config.
            base_url: Base URL for API. For OpenRouter, use https://openrouter.ai/api/v1
            max_retries: Maximum retry attempts on validation failures. Defaults to INSTRUCTOR_MAX_RETRIES.
            timeout: Request timeout in seconds. Defaults to INSTRUCTOR_TIMEOUT.
            **kwargs: Additional arguments passed to AsyncOpenAI client

        Returns:
            Instructor-wrapped async client if enabled, otherwise standard AsyncOpenAI client

        Example:
            >>> import asyncio
            >>> from ai.structured_outputs import InstructorClientFactory
            >>> from ai.response_models import PerspectiveAnalysisResult
            >>>
            >>> async def analyze():
            ...     client = InstructorClientFactory.create_async_client(
            ...         api_key=config.openrouter_api_key,
            ...         base_url="https://openrouter.ai/api/v1"
            ...     )
            ...     result = await client.chat.completions.create(
            ...         model="anthropic/claude-3.5-sonnet",
            ...         response_model=PerspectiveAnalysisResult,
            ...         messages=[{"role": "user", "content": "Analyze perspectives..."}]
            ...     )
            ...     return result
            >>>
            >>> result = asyncio.run(analyze())
        """
        config = get_config()
        if api_key is None:
            api_key = config.openai_api_key
        if max_retries is None:
            max_retries = config.instructor_max_retries
        if timeout is None:
            timeout = config.instructor_timeout
        async_openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url, max_retries=max_retries, timeout=timeout, **kwargs)
        if InstructorClientFactory.is_enabled():
            logger.debug(f'Creating async Instructor client with max_retries={max_retries}, timeout={timeout}')
            return instructor.from_openai(async_openai_client)
        else:
            logger.debug('Instructor disabled, returning standard async OpenAI client')
            return async_openai_client

    @staticmethod
    def create_openrouter_client(max_retries: int | None=None, timeout: int | None=None, **kwargs: Any) -> OpenAI | Instructor:
        """Convenience method to create an OpenRouter client with Instructor support.

        Automatically configures base_url and api_key for OpenRouter.

        Args:
            max_retries: Maximum retry attempts. Defaults to INSTRUCTOR_MAX_RETRIES.
            timeout: Request timeout in seconds. Defaults to INSTRUCTOR_TIMEOUT.
            **kwargs: Additional arguments passed to OpenAI client

        Returns:
            Instructor-wrapped OpenRouter client if enabled, otherwise standard client

        Example:
            >>> client = InstructorClientFactory.create_openrouter_client()
            >>> result = client.chat.completions.create(
            ...     model="anthropic/claude-3.5-sonnet",
            ...     response_model=FallacyAnalysisResult,
            ...     messages=[...]
            ... )
        """
        config = get_config()
        return InstructorClientFactory.create_client(api_key=config.openrouter_api_key, base_url='https://openrouter.ai/api/v1', max_retries=max_retries, timeout=timeout, **kwargs)

    @staticmethod
    def create_async_openrouter_client(max_retries: int | None=None, timeout: int | None=None, **kwargs: Any) -> AsyncOpenAI | Any:
        """Convenience method to create an async OpenRouter client with Instructor support.

        Async variant of create_openrouter_client().

        Args:
            max_retries: Maximum retry attempts. Defaults to INSTRUCTOR_MAX_RETRIES.
            timeout: Request timeout in seconds. Defaults to INSTRUCTOR_TIMEOUT.
            **kwargs: Additional arguments passed to AsyncOpenAI client

        Returns:
            Instructor-wrapped async OpenRouter client if enabled, otherwise standard client

        Example:
            >>> async def analyze():
            ...     client = InstructorClientFactory.create_async_openrouter_client()
            ...     result = await client.chat.completions.create(
            ...         model="anthropic/claude-3.5-sonnet",
            ...         response_model=PerspectiveAnalysisResult,
            ...         messages=[...]
            ...     )
            ...     return result
        """
        config = get_config()
        return InstructorClientFactory.create_async_client(api_key=config.openrouter_api_key, base_url='https://openrouter.ai/api/v1', max_retries=max_retries, timeout=timeout, **kwargs)
__all__ = ['INSTRUCTOR_AVAILABLE', 'InstructorClientFactory']