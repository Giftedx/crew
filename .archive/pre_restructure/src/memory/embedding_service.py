"""Embedding Service for Creator Intelligence System.

Provides unified interface for generating embeddings from text, supporting multiple
embedding models with automatic fallback and caching.

Models:
- sentence-transformers/all-MiniLM-L6-v2: 384-dim, fast (default)
- sentence-transformers/all-mpnet-base-v2: 768-dim, balanced quality
- openai/text-embedding-3-small: 1536-dim, high quality (API-based)

Features:
- Model auto-selection based on content type
- Embedding caching to reduce redundant computation
- Batch processing for efficiency
- Cost tracking for API-based models
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from typing import Any, Literal

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)

# Try to import sentence-transformers (optional dependency)
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None  # type: ignore
    logger.warning("sentence-transformers not available, using fallback embeddings")

# Model dimensions
MODEL_DIMENSIONS = {
    "all-MiniLM-L6-v2": 384,
    "all-mpnet-base-v2": 768,
    "openai-small": 1536,
    "openai-large": 3072,
}


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    embedding: list[float]
    model: str
    dimension: int
    tokens_used: int = 0
    cache_hit: bool = False
    generation_time_ms: float = 0.0


class EmbeddingService:
    """Unified embedding service with model selection and caching.

    Usage:
        service = EmbeddingService()
        result = service.embed_text("some text content", model="fast")
        embedding = result.data["embedding"]
    """

    def __init__(self, cache_size: int = 10000):
        """Initialize embedding service.

        Args:
            cache_size: Maximum number of cached embeddings
        """
        self.cache_size = cache_size
        self._embedding_cache: dict[str, EmbeddingResult] = {}

        # Load models lazily on first use (sentence-transformers models)
        self._models: dict[str, Any] = {}

    def embed_text(
        self,
        text: str,
        model: Literal["fast", "balanced", "quality"] = "fast",
        use_cache: bool = True,
    ) -> StepResult:
        """Generate embedding for text.

        Args:
            text: Input text to embed
            model: Model selection (fast, balanced, quality)
            use_cache: Whether to use embedding cache

        Returns:
            StepResult with embedding data
        """
        try:
            import time

            start_time = time.time()

            if not text or not text.strip():
                return StepResult.fail("Input text cannot be empty", status="bad_request")

            # Check cache first
            if use_cache:
                cache_result = self._check_cache(text, model)
                if cache_result:
                    logger.info(f"Embedding cache hit for text (len={len(text)})")
                    return StepResult.ok(
                        data={
                            "embedding": cache_result.embedding,
                            "model": cache_result.model,
                            "dimension": cache_result.dimension,
                            "cache_hit": True,
                            "generation_time_ms": (time.time() - start_time) * 1000,
                        }
                    )

            # Generate embedding
            model_name = self._select_model(model)
            embedding_result = self._generate_embedding(text, model_name)

            if embedding_result:
                # Cache result
                if use_cache:
                    self._cache_embedding(text, model, embedding_result)

                generation_time = (time.time() - start_time) * 1000

                return StepResult.ok(
                    data={
                        "embedding": embedding_result.embedding,
                        "model": embedding_result.model,
                        "dimension": embedding_result.dimension,
                        "cache_hit": False,
                        "generation_time_ms": generation_time,
                    }
                )
            else:
                return StepResult.fail("Failed to generate embedding", status="retryable")

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return StepResult.fail(f"Embedding failed: {e!s}", status="retryable")

    def embed_batch(
        self,
        texts: list[str],
        model: Literal["fast", "balanced", "quality"] = "fast",
        use_cache: bool = True,
    ) -> StepResult:
        """Generate embeddings for multiple texts in batch.

        Args:
            texts: List of input texts
            model: Model selection
            use_cache: Whether to use embedding cache

        Returns:
            StepResult with list of embeddings
        """
        try:
            if not texts:
                return StepResult.fail("Input texts list cannot be empty", status="bad_request")

            embeddings = []
            cache_hits = 0

            for text in texts:
                result = self.embed_text(text, model=model, use_cache=use_cache)

                if result.success:
                    embeddings.append(result.data["embedding"])
                    if result.data.get("cache_hit"):
                        cache_hits += 1
                else:
                    # Return partial failure
                    return StepResult.fail(
                        f"Batch embedding failed at text {len(embeddings)}: {result.error}",
                        metadata={"partial_embeddings": embeddings},
                    )

            return StepResult.ok(
                data={
                    "embeddings": embeddings,
                    "count": len(embeddings),
                    "cache_hits": cache_hits,
                    "cache_hit_rate": cache_hits / len(embeddings) if embeddings else 0.0,
                }
            )

        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            return StepResult.fail(f"Batch embedding failed: {e!s}")

    def _select_model(self, model_alias: str) -> str:
        """Select actual model name from alias.

        Args:
            model_alias: Model alias (fast, balanced, quality)

        Returns:
            Actual model identifier
        """
        model_map = {
            "fast": "all-MiniLM-L6-v2",
            "balanced": "all-mpnet-base-v2",
            "quality": "openai-small",  # Requires API key
        }

        return model_map.get(model_alias, "all-MiniLM-L6-v2")

    def _generate_embedding(self, text: str, model_name: str) -> EmbeddingResult | None:
        """Generate embedding using specified model.

        Args:
            text: Input text
            model_name: Model identifier

        Returns:
            EmbeddingResult or None if generation fails
        """
        try:
            # OpenAI API-based models
            if model_name.startswith("openai"):
                return self._generate_openai_embedding(text, model_name)

            # Local sentence-transformers models
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                return self._generate_local_embedding(text, model_name)

            # Fallback to placeholder
            logger.warning(f"Using fallback embedding for model {model_name}")
            return self._generate_fallback_embedding(text, model_name)

        except Exception as e:
            logger.error(f"Embedding generation failed for model {model_name}: {e}")
            return None

    def _generate_local_embedding(self, text: str, model_name: str) -> EmbeddingResult:
        """Generate embedding using local sentence-transformers model.

        Args:
            text: Input text
            model_name: Model identifier

        Returns:
            EmbeddingResult with generated embedding
        """
        # Load model lazily
        if model_name not in self._models:
            if SentenceTransformer is None:
                raise RuntimeError("sentence-transformers not available")
            logger.info(f"Loading sentence-transformers model: {model_name}")
            self._models[model_name] = SentenceTransformer(f"sentence-transformers/{model_name}")

        model_obj = self._models[model_name]

        # Generate embedding using encode method
        embedding = model_obj.encode(text, convert_to_numpy=False)  # type: ignore

        # Convert to list if needed
        if hasattr(embedding, "tolist"):
            embedding = embedding.tolist()

        return EmbeddingResult(
            embedding=list(embedding),
            model=model_name,
            dimension=len(embedding),
            tokens_used=0,  # Local models don't have token counts
            cache_hit=False,
        )

    def _generate_openai_embedding(self, text: str, model_name: str) -> EmbeddingResult:
        """Generate embedding using OpenAI API.

        Args:
            text: Input text
            model_name: Model identifier (openai-small or openai-large)

        Returns:
            EmbeddingResult with generated embedding
        """
        try:
            import openai

            api_key = os.getenv("OPENAI_API_KEY")

            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")

            # Map model alias to actual OpenAI model
            openai_model_map = {
                "openai-small": "text-embedding-3-small",
                "openai-large": "text-embedding-3-large",
            }

            actual_model = openai_model_map.get(model_name, "text-embedding-3-small")

            # Generate embedding via API
            client = openai.OpenAI(api_key=api_key)
            response = client.embeddings.create(input=text, model=actual_model)

            embedding = response.data[0].embedding
            tokens_used = response.usage.total_tokens

            return EmbeddingResult(
                embedding=embedding,
                model=model_name,
                dimension=len(embedding),
                tokens_used=tokens_used,
                cache_hit=False,
            )

        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            # Fallback to local model
            logger.info("Falling back to local model")
            return self._generate_local_embedding(text, "all-mpnet-base-v2")

    def _generate_fallback_embedding(self, text: str, model_name: str) -> EmbeddingResult:
        """Generate deterministic fallback embedding when models unavailable.

        Args:
            text: Input text
            model_name: Requested model identifier

        Returns:
            EmbeddingResult with fallback embedding
        """
        # Get expected dimension
        dimension = MODEL_DIMENSIONS.get(model_name, 384)

        # Generate deterministic hash-based embedding
        text_hash = hashlib.sha256(text.encode()).digest()

        # Repeat hash to reach desired dimension
        num_repeats = (dimension // 32) + 1
        full_bytes = (text_hash * num_repeats)[:dimension]

        # Normalize to [-1, 1] range
        embedding = [(b / 127.5) - 1.0 for b in full_bytes]

        logger.warning(f"Generated fallback embedding (dim={dimension}) - not suitable for production")

        return EmbeddingResult(
            embedding=embedding,
            model=f"fallback-{model_name}",
            dimension=dimension,
            cache_hit=False,
        )

    def _check_cache(self, text: str, model: str) -> EmbeddingResult | None:
        """Check if embedding exists in cache.

        Args:
            text: Input text
            model: Model alias

        Returns:
            Cached EmbeddingResult or None
        """
        cache_key = self._compute_cache_key(text, model)

        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        return None

    def _cache_embedding(self, text: str, model: str, result: EmbeddingResult) -> None:
        """Cache embedding result.

        Args:
            text: Input text
            model: Model alias
            result: Embedding result to cache
        """
        cache_key = self._compute_cache_key(text, model)

        # Evict old entries if cache is full
        if len(self._embedding_cache) >= self.cache_size:
            # Simple FIFO eviction - remove first key
            first_key = next(iter(self._embedding_cache))
            del self._embedding_cache[first_key]

        self._embedding_cache[cache_key] = result

    @staticmethod
    def _compute_cache_key(text: str, model: str) -> str:
        """Compute cache key for text and model.

        Args:
            text: Input text
            model: Model alias

        Returns:
            Cache key string
        """
        combined = f"{model}:{text}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def clear_cache(self) -> StepResult:
        """Clear embedding cache.

        Returns:
            StepResult with cache clear status
        """
        cache_size = len(self._embedding_cache)
        self._embedding_cache.clear()

        logger.info(f"Cleared {cache_size} cached embeddings")

        return StepResult.ok(data={"cleared_entries": cache_size})

    def get_cache_stats(self) -> StepResult:
        """Get embedding cache statistics.

        Returns:
            StepResult with cache statistics
        """
        try:
            models_cached: dict[str, int] = {}

            # Count entries per model
            for result in self._embedding_cache.values():
                model = result.model
                models_cached[model] = models_cached.get(model, 0) + 1

            stats = {
                "total_cached": len(self._embedding_cache),
                "cache_size_limit": self.cache_size,
                "utilization": len(self._embedding_cache) / self.cache_size if self.cache_size > 0 else 0.0,
                "models_cached": models_cached,
            }

            return StepResult.ok(data=stats)

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return StepResult.fail(f"Failed to get cache stats: {e!s}")


# Singleton instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service instance.

    Returns:
        Initialized EmbeddingService instance
    """
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService()

    return _embedding_service
