"""Tests for Embedding Service."""

from __future__ import annotations

from memory.embedding_service import EmbeddingService, get_embedding_service


class TestEmbeddingService:
    """Test embedding service functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = EmbeddingService(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.service.cache_size == 100
        assert len(self.service._embedding_cache) == 0
        assert len(self.service._models) == 0

    def test_embed_text_with_fallback(self) -> None:
        """Test embedding generation with fallback."""
        result = self.service.embed_text(
            text="This is a test sentence for embedding generation.",
            model="fast",
            use_cache=True,
        )

        assert result.success
        assert result.data is not None
        assert "embedding" in result.data
        assert "dimension" in result.data
        assert "cache_hit" in result.data

        # First call should not be cache hit
        assert result.data["cache_hit"] is False

        # Embedding should have correct dimension (384 for MiniLM)
        embedding = result.data["embedding"]
        assert isinstance(embedding, list)
        assert len(embedding) in [384, 768]  # MiniLM or mpnet

    def test_embed_empty_text(self) -> None:
        """Test handling of empty text."""
        result = self.service.embed_text(text="", model="fast")

        assert not result.success
        assert result.status == "bad_request"
        assert "empty" in result.error.lower()

    def test_embedding_cache_hit(self) -> None:
        """Test embedding cache functionality."""
        text = "Cached test sentence"

        # First call - cache miss
        result1 = self.service.embed_text(text, model="fast", use_cache=True)
        assert result1.success
        assert result1.data["cache_hit"] is False

        # Second call - should be cache hit
        result2 = self.service.embed_text(text, model="fast", use_cache=True)
        assert result2.success
        assert result2.data["cache_hit"] is True

        # Embeddings should be identical
        assert result1.data["embedding"] == result2.data["embedding"]

    def test_embed_batch(self) -> None:
        """Test batch embedding generation."""
        texts = [
            "First test sentence",
            "Second test sentence",
            "Third test sentence",
        ]

        result = self.service.embed_batch(texts, model="fast", use_cache=True)

        assert result.success
        assert result.data is not None
        assert "embeddings" in result.data
        assert len(result.data["embeddings"]) == 3
        assert result.data["count"] == 3

    def test_embed_batch_empty_list(self) -> None:
        """Test batch embedding with empty list."""
        result = self.service.embed_batch([], model="fast")

        assert not result.success
        assert result.status == "bad_request"

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some cached embeddings
        self.service.embed_text("Test 1", use_cache=True)
        self.service.embed_text("Test 2", use_cache=True)

        assert len(self.service._embedding_cache) > 0

        # Clear cache
        result = self.service.clear_cache()

        assert result.success
        assert result.data["cleared_entries"] > 0
        assert len(self.service._embedding_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        # Add some cached embeddings
        self.service.embed_text("Test 1", model="fast", use_cache=True)
        self.service.embed_text("Test 2", model="balanced", use_cache=True)

        result = self.service.get_cache_stats()

        assert result.success
        assert result.data is not None
        assert "total_cached" in result.data
        assert "cache_size_limit" in result.data
        assert "utilization" in result.data
        assert "models_cached" in result.data

        assert result.data["total_cached"] >= 2
        assert result.data["cache_size_limit"] == 100

    def test_model_selection(self) -> None:
        """Test model selection logic."""
        assert self.service._select_model("fast") == "all-MiniLM-L6-v2"
        assert self.service._select_model("balanced") == "all-mpnet-base-v2"
        assert self.service._select_model("quality") == "openai-small"
        assert self.service._select_model("unknown") == "all-MiniLM-L6-v2"  # Default

    def test_cache_eviction(self) -> None:
        """Test cache eviction when full."""
        # Create service with small cache
        service = EmbeddingService(cache_size=3)

        # Fill cache beyond capacity
        service.embed_text("Text 1", use_cache=True)
        service.embed_text("Text 2", use_cache=True)
        service.embed_text("Text 3", use_cache=True)
        service.embed_text("Text 4", use_cache=True)  # Should trigger eviction

        # Cache should not exceed limit
        assert len(service._embedding_cache) <= 3

    def test_cache_bypass(self) -> None:
        """Test bypassing cache."""
        text = "Test sentence"

        # First call with cache
        result1 = self.service.embed_text(text, use_cache=True)
        assert result1.success

        # Second call bypassing cache
        result2 = self.service.embed_text(text, use_cache=False)
        assert result2.success
        assert result2.data["cache_hit"] is False


class TestEmbeddingServiceSingleton:
    """Test singleton instance management."""

    def test_get_embedding_service(self) -> None:
        """Test getting singleton instance."""
        service1 = get_embedding_service()
        service2 = get_embedding_service()

        # Should return same instance
        assert service1 is service2
        assert isinstance(service1, EmbeddingService)
