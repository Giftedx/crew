"""Tests for Creator Intelligence Collection Management."""

from __future__ import annotations

import pytest

from memory.creator_intelligence_collections import (
    COLLECTION_CONFIGS,
    CachedQuery,
    CollectionConfig,
    CreatorIntelligenceCollectionManager,
    get_collection_manager,
)
from memory.enhanced_vector_store import EnhancedVectorStore, SearchResult


class TestCollectionConfig:
    """Test collection configuration."""

    def test_default_dimension(self):
        """Test default embedding dimension."""
        config = CollectionConfig(
            name="test_collection",
            description="Test collection",
        )

        assert config.dimension == 384  # Default model dimension

    def test_custom_embedding_model(self):
        """Test custom embedding model dimension."""
        config = CollectionConfig(
            name="test_collection",
            description="Test collection",
            embedding_model="sentence-transformers/all-mpnet-base-v2",
        )

        assert config.dimension == 768

    def test_all_predefined_configs(self):
        """Test all predefined collection configurations."""
        assert "episodes" in COLLECTION_CONFIGS
        assert "segments" in COLLECTION_CONFIGS
        assert "claims" in COLLECTION_CONFIGS
        assert "quotes" in COLLECTION_CONFIGS
        assert "topics" in COLLECTION_CONFIGS

        # Verify each config has required fields
        for config in COLLECTION_CONFIGS.values():
            assert config.name
            assert config.description
            assert config.dimension > 0
            assert config.payload_schema


class TestCachedQuery:
    """Test cached query functionality."""

    def test_cache_expiry(self):
        """Test cache entry expiration."""
        import time

        cached = CachedQuery(
            query_hash="test_hash",
            query_embedding=[0.1, 0.2, 0.3],
            results=[],
            cache_time=time.time() - 3700,  # 1 hour and 100 seconds ago
            ttl_seconds=3600,  # 1 hour TTL
        )

        assert cached.is_expired()

    def test_cache_not_expired(self):
        """Test cache entry not expired."""
        import time

        cached = CachedQuery(
            query_hash="test_hash",
            query_embedding=[0.1, 0.2, 0.3],
            results=[],
            cache_time=time.time(),
            ttl_seconds=3600,
        )

        assert not cached.is_expired()


class TestCreatorIntelligenceCollectionManager:
    """Test collection manager functionality."""

    @pytest.fixture
    def manager(self):
        """Create test collection manager with in-memory vector store."""
        # Use in-memory Qdrant for testing
        vector_store = EnhancedVectorStore(url=":memory:")
        return CreatorIntelligenceCollectionManager(
            vector_store=vector_store,
            enable_semantic_cache=True,
        )

    def test_initialization(self, manager):
        """Test manager initialization."""
        assert manager.vector_store is not None
        assert manager.enable_semantic_cache is True
        assert len(manager._query_cache) == 0
        assert len(manager._initialized_collections) == 0

    def test_initialize_collections(self, manager):
        """Test collection initialization."""
        result = manager.initialize_collections(tenant="test_tenant", workspace="test_workspace")

        assert result.success
        assert result.data is not None
        assert result.data["total"] > 0
        assert "initialized" in result.data

    def test_namespace_generation(self, manager):
        """Test tenant-aware namespace generation."""
        namespace = manager._get_namespace(
            tenant="test_tenant",
            workspace="test_workspace",
            collection_name="creator_episodes",
        )

        assert namespace == "test_tenant:test_workspace:creator_episodes"

    def test_query_hash_computation(self):
        """Test deterministic query hash computation."""
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        namespace = "test:main:episodes"
        limit = 10

        hash1 = CreatorIntelligenceCollectionManager._compute_query_hash(embedding, namespace, limit)
        hash2 = CreatorIntelligenceCollectionManager._compute_query_hash(embedding, namespace, limit)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest

    def test_cosine_similarity(self):
        """Test cosine similarity computation."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]

        similarity = CreatorIntelligenceCollectionManager._cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.001  # Perfect similarity

        vec3 = [1.0, 0.0, 0.0]
        vec4 = [0.0, 1.0, 0.0]

        similarity2 = CreatorIntelligenceCollectionManager._cosine_similarity(vec3, vec4)
        assert abs(similarity2 - 0.0) < 0.001  # Orthogonal vectors

    def test_cosine_similarity_different_lengths(self):
        """Test cosine similarity with different length vectors."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0]

        similarity = CreatorIntelligenceCollectionManager._cosine_similarity(vec1, vec2)
        assert similarity == 0.0

    def test_query_with_invalid_collection(self, manager):
        """Test query with invalid collection type."""
        result = manager.query_with_cache(
            collection_type="invalid_type",  # type: ignore
            query_embedding=[0.1, 0.2, 0.3],
            query_text="test query",
            tenant="test_tenant",
            workspace="test_workspace",
        )

        assert not result.success
        assert result.status == "bad_request"
        assert "Invalid collection type" in result.error

    def test_semantic_cache_miss(self, manager):
        """Test semantic cache miss on first query."""
        # Initialize collections first
        manager.initialize_collections(tenant="test_tenant", workspace="test_workspace")

        result = manager.query_with_cache(
            collection_type="episodes",
            query_embedding=[0.1] * 768,  # Match dimension for mpnet model
            query_text="test query",
            tenant="test_tenant",
            workspace="test_workspace",
            limit=5,
        )

        assert result.success
        assert result.data is not None
        assert result.data["cache_hit"] is False

    def test_clear_semantic_cache(self, manager):
        """Test clearing semantic cache."""
        # Add some dummy cache entries
        manager._query_cache["test1"] = CachedQuery(
            query_hash="test1",
            query_embedding=[0.1],
            results=[],
            cache_time=0,
        )

        manager._query_cache["test2"] = CachedQuery(
            query_hash="test2",
            query_embedding=[0.2],
            results=[],
            cache_time=0,
        )

        assert len(manager._query_cache) == 2

        result = manager.clear_semantic_cache()

        assert result.success
        assert result.data["cleared_entries"] == 2
        assert len(manager._query_cache) == 0

    def test_get_collection_stats_invalid_type(self, manager):
        """Test getting stats for invalid collection type."""
        result = manager.get_collection_stats(
            collection_type="invalid",  # type: ignore
            tenant="test_tenant",
            workspace="test_workspace",
        )

        assert not result.success
        assert result.status == "bad_request"

    def test_factory_function(self):
        """Test factory function for creating manager."""
        manager = get_collection_manager(enable_semantic_cache=False)

        assert isinstance(manager, CreatorIntelligenceCollectionManager)
        assert manager.enable_semantic_cache is False


class TestSemanticCaching:
    """Test semantic caching functionality."""

    @pytest.fixture
    def manager(self):
        """Create manager with caching enabled."""
        vector_store = EnhancedVectorStore(url=":memory:")
        return CreatorIntelligenceCollectionManager(
            vector_store=vector_store,
            enable_semantic_cache=True,
        )

    def test_cache_query_results(self, manager):
        """Test caching query results."""
        query_embedding = [0.1, 0.2, 0.3]
        namespace = "test:main:episodes"
        results = [
            SearchResult(
                id="1",
                payload={"title": "Test Episode"},
                dense_score=0.9,
            )
        ]

        manager._cache_query_results(query_embedding, namespace, results, limit=10)

        assert len(manager._query_cache) == 1

    def test_check_semantic_cache_hit(self, manager):
        """Test semantic cache hit detection."""
        query_embedding = [0.1, 0.2, 0.3]
        namespace = "test:main:episodes"
        results = [
            SearchResult(
                id="1",
                payload={"title": "Test Episode"},
                dense_score=0.9,
            )
        ]

        # Cache results
        manager._cache_query_results(query_embedding, namespace, results, limit=10)

        # Check for exact same query
        cached = manager._check_semantic_cache(query_embedding, namespace, 10)

        assert cached is not None
        assert len(cached.results) == 1

    def test_check_semantic_cache_miss(self, manager):
        """Test semantic cache miss."""
        query_embedding1 = [1.0, 0.0, 0.0]
        query_embedding2 = [0.0, 1.0, 0.0]  # Orthogonal, similarity = 0
        namespace = "test:main:episodes"

        # Cache first query
        manager._cache_query_results(query_embedding1, namespace, [], limit=10)

        # Check for different query
        cached = manager._check_semantic_cache(query_embedding2, namespace, 10)

        assert cached is None

    def test_evict_expired_cache(self, manager):
        """Test eviction of expired cache entries."""
        import time

        # Add expired entry
        manager._query_cache["expired"] = CachedQuery(
            query_hash="expired",
            query_embedding=[0.1],
            results=[],
            cache_time=time.time() - 7200,  # 2 hours ago
            ttl_seconds=3600,  # 1 hour TTL
        )

        # Add valid entry
        manager._query_cache["valid"] = CachedQuery(
            query_hash="valid",
            query_embedding=[0.2],
            results=[],
            cache_time=time.time(),
        )

        assert len(manager._query_cache) == 2

        manager._evict_expired_cache()

        assert len(manager._query_cache) == 1
        assert "valid" in manager._query_cache
        assert "expired" not in manager._query_cache
