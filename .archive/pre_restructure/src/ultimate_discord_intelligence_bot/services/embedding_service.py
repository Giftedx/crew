"""Embedding service for vector operations.

This module provides embedding generation capabilities for the multi-agent
orchestration system, supporting both OpenAI and local embedding models.
"""

from __future__ import annotations

import logging
from typing import Any

import openai
from openai import AsyncOpenAI

from ..step_result import StepResult
from ..tenancy.helpers import require_tenant


logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using OpenAI or local models."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "text-embedding-3-small",
        batch_size: int = 100,
        timeout: int = 30,
    ):
        """Initialize the embedding service.

        Args:
            api_key: OpenAI API key (optional, uses environment if not provided)
            base_url: Custom base URL for OpenAI client
            model: Embedding model to use
            batch_size: Maximum batch size for embedding generation
            timeout: Request timeout in seconds
        """
        self.model = model
        self.batch_size = batch_size
        self.timeout = timeout

        # Initialize OpenAI client
        client_kwargs: dict[str, Any] = {}
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = AsyncOpenAI(**client_kwargs)

    @require_tenant(strict_flag_enabled=False)
    async def generate_embedding(self, text: str, tenant: str, workspace: str) -> StepResult:
        """Generate embedding for a single text.

        Args:
            text: Text to embed
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult containing the embedding vector
        """
        try:
            if not text or not text.strip():
                return StepResult.fail("Text cannot be empty")

            # Generate embedding
            response = await self.client.embeddings.create(model=self.model, input=text.strip(), timeout=self.timeout)

            embedding = response.data[0].embedding

            logger.debug(
                "Generated embedding for text (length: %d, tenant: %s, workspace: %s)", len(text), tenant, workspace
            )

            return StepResult.ok(data=embedding)

        except openai.RateLimitError as e:
            logger.warning("OpenAI rate limit exceeded: %s", str(e))
            return StepResult.fail(f"Rate limit exceeded: {e!s}", status="rate_limited")
        except openai.APIError as e:
            logger.error("OpenAI API error: %s", str(e))
            return StepResult.fail(f"API error: {e!s}", status="retryable")
        except Exception as e:
            logger.error("Unexpected error generating embedding: %s", str(e))
            return StepResult.fail(f"Embedding generation failed: {e!s}")

    @require_tenant(strict_flag_enabled=False)
    async def generate_embeddings_batch(self, texts: list[str], tenant: str, workspace: str) -> StepResult:
        """Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult containing list of embedding vectors
        """
        try:
            if not texts:
                return StepResult.fail("Texts list cannot be empty")

            # Filter out empty texts
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            if not valid_texts:
                return StepResult.fail("No valid texts to embed")

            embeddings = []

            # Process in batches
            for i in range(0, len(valid_texts), self.batch_size):
                batch = valid_texts[i : i + self.batch_size]

                try:
                    response = await self.client.embeddings.create(model=self.model, input=batch, timeout=self.timeout)

                    batch_embeddings = [item.embedding for item in response.data]
                    embeddings.extend(batch_embeddings)

                    logger.debug(
                        "Generated batch embeddings (batch size: %d, total: %d, tenant: %s, workspace: %s)",
                        len(batch),
                        len(embeddings),
                        tenant,
                        workspace,
                    )

                except openai.RateLimitError as e:
                    logger.warning("Rate limit in batch %d: %s", i // self.batch_size, str(e))
                    # Add empty embeddings for failed batch
                    embeddings.extend([[] for _ in batch])
                except Exception as e:
                    logger.error("Error in batch %d: %s", i // self.batch_size, str(e))
                    # Add empty embeddings for failed batch
                    embeddings.extend([[] for _ in batch])

            return StepResult.ok(data=embeddings)

        except Exception as e:
            logger.error("Unexpected error in batch embedding generation: %s", str(e))
            return StepResult.fail(f"Batch embedding generation failed: {e!s}")

    def count_tokens(self, text: str, model: str | None = None) -> int:
        """Count tokens in text for a given model.

        Args:
            text: Text to count tokens for
            model: Model to use for token counting (defaults to self.model)

        Returns:
            Number of tokens
        """
        try:
            # Use tiktoken for token counting
            import tiktoken

            model_name = model or self.model
            encoding = tiktoken.encoding_for_model(model_name)
            return len(encoding.encode(text))

        except Exception as e:
            logger.warning("Token counting failed, using approximation: %s", str(e))
            # Fallback to character-based approximation
            return len(text) // 4

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this service.

        Returns:
            Embedding dimension
        """
        # OpenAI text-embedding-3-small produces 1536-dimensional embeddings
        if "3-small" in self.model:
            return 1536
        elif "3-large" in self.model:
            return 3072
        else:
            # Default to 1536 for unknown models
            return 1536

    async def health_check(self) -> StepResult:
        """Perform health check on the embedding service.

        Returns:
            StepResult with health status
        """
        try:
            # Test with a simple embedding
            test_text = "Health check test"
            result = await self.generate_embedding(test_text, "health_check", "test")

            if result.success:
                return StepResult.ok(
                    data={
                        "status": "healthy",
                        "model": self.model,
                        "dimension": self.get_embedding_dimension(),
                        "batch_size": self.batch_size,
                    }
                )
            else:
                return StepResult.fail(f"Health check failed: {result.error}")

        except Exception as e:
            return StepResult.fail(f"Health check error: {e!s}")


def create_embedding_service() -> EmbeddingService:
    """Create an embedding service instance with settings from environment.

    Returns:
        Configured EmbeddingService instance
    """
    from ..settings import get_settings

    settings = get_settings()

    return EmbeddingService(
        api_key=settings.openai_api_key,
        model=getattr(settings, "embedding_model", "text-embedding-3-small"),
        batch_size=getattr(settings, "embedding_batch_size", 100),
        timeout=getattr(settings, "embedding_timeout", 30),
    )
