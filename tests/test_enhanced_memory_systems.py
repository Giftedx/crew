"""
Tests for enhanced memory systems implementation.

This module tests multi-modal embeddings, advanced compaction algorithms,
and cross-tenant similarity prevention for comprehensive memory optimization.
"""

import asyncio
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

from ultimate_discord_intelligence_bot.core.memory import (
    AdvancedMemoryCompactor,
    CompactionConfig,
    CompactionStrategy,
    CompactionTrigger,
    CrossTenantConfig,
    CrossTenantSimilarityDetector,
    EmbeddingConfig,
    EmbeddingType,
    IsolationStrategy,
    MultiModalEmbeddingGenerator,
)


class TestMultiModalEmbeddingGenerator:
    """Test multi-modal embedding generator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = EmbeddingConfig(
            embedding_dimension=128,  # Smaller for testing
            max_text_length=1000,
            enable_caching=True,
        )
        self.generator = MultiModalEmbeddingGenerator(self.config)

    @pytest.mark.asyncio
    async def test_text_embedding_generation(self):
        """Test text embedding generation."""
        text = "This is a test text for embedding generation"

        result = await self.generator.generate_text_embedding(text)

        assert result.embedding_type == EmbeddingType.TEXT
        assert result.embedding.shape == (self.config.embedding_dimension,)
        assert result.content_hash is not None
        assert result.processing_time > 0
        assert result.confidence_score == 1.0

    @pytest.mark.asyncio
    async def test_image_embedding_generation(self):
        """Test image embedding generation."""
        # Create a test image
        image = Image.new("RGB", (224, 224), color="red")

        result = await self.generator.generate_image_embedding(image)

        assert result.embedding_type == EmbeddingType.IMAGE
        assert result.embedding.shape == (self.config.embedding_dimension,)
        assert result.content_hash is not None
        assert result.processing_time > 0
        assert result.confidence_score == 1.0

    @pytest.mark.asyncio
    async def test_audio_embedding_generation(self):
        """Test audio embedding generation."""
        # Create test audio data (file path)
        audio_path = "test_audio.wav"

        result = await self.generator.generate_audio_embedding(audio_path)

        assert result.embedding_type == EmbeddingType.AUDIO
        assert result.embedding.shape == (self.config.embedding_dimension,)
        assert result.content_hash is not None
        assert result.processing_time > 0
        assert result.confidence_score == 1.0

    @pytest.mark.asyncio
    async def test_multimodal_embedding_generation(self):
        """Test multi-modal embedding generation."""
        text = "Test text content"
        image = Image.new("RGB", (224, 224), color="blue")

        result = await self.generator.generate_multimodal_embedding(
            text=text, image_data=image, content_id="test_multimodal"
        )

        assert result.has_text
        assert result.has_image
        assert not result.has_audio
        assert result.modality_count == 2
        assert result.content_id == "test_multimodal"
        assert result.fused_embedding is not None
        assert result.fused_embedding.shape == (self.config.embedding_dimension,)

    @pytest.mark.asyncio
    async def test_embedding_caching(self):
        """Test embedding caching functionality."""
        text = "Test caching text"

        # Generate embedding twice
        result1 = await self.generator.generate_text_embedding(text)
        result2 = await self.generator.generate_text_embedding(text)

        # Should be the same embedding (cached)
        assert np.array_equal(result1.embedding, result2.embedding)
        assert result1.content_hash == result2.content_hash

    def test_similarity_calculation(self):
        """Test similarity calculation between embeddings."""
        # Create test embeddings
        embedding1 = np.random.normal(0, 1, self.config.embedding_dimension)
        embedding2 = np.random.normal(0, 1, self.config.embedding_dimension)

        # Normalize embeddings
        embedding1 = embedding1 / np.linalg.norm(embedding1)
        embedding2 = embedding2 / np.linalg.norm(embedding2)

        similarity = self.generator.calculate_similarity(embedding1, embedding2)

        assert 0.0 <= similarity <= 1.0

    def test_cache_statistics(self):
        """Test cache statistics functionality."""
        stats = self.generator.get_cache_stats()

        assert "total_entries" in stats
        assert "text_entries" in stats
        assert "image_entries" in stats
        assert "audio_entries" in stats
        assert "cache_hit_rate" in stats

    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        # Add some entries to cache
        asyncio.run(self.generator.generate_text_embedding("test"))

        # Clear cache
        self.generator.clear_cache()

        # Check cache is empty
        stats = self.generator.get_cache_stats()
        assert stats["total_entries"] == 0


class TestAdvancedMemoryCompactor:
    """Test advanced memory compactor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = CompactionConfig(
            max_memory_usage_mb=10.0,  # Small for testing
            max_entries=100,
            compaction_ratio=0.2,
            similarity_threshold=0.9,
        )
        self.compactor = AdvancedMemoryCompactor(self.config)

    @pytest.mark.asyncio
    async def test_add_and_get_entry(self):
        """Test adding and retrieving entries."""
        entry_id = "test_entry"
        embedding = np.random.normal(0, 1, 128)
        content = "test content"

        await self.compactor.add_entry(entry_id, embedding, content)

        retrieved_entry = await self.compactor.get_entry(entry_id)
        assert retrieved_entry is not None
        assert retrieved_entry.id == entry_id
        assert np.array_equal(retrieved_entry.embedding, embedding)
        assert retrieved_entry.content == content

    @pytest.mark.asyncio
    async def test_access_tracking(self):
        """Test access tracking functionality."""
        entry_id = "test_entry"
        embedding = np.random.normal(0, 1, 128)

        await self.compactor.add_entry(entry_id, embedding, "content")

        # Get entry multiple times
        for _ in range(5):
            await self.compactor.get_entry(entry_id)

        entry = await self.compactor.get_entry(entry_id)
        assert entry.access_count == 6  # 5 + initial add
        assert entry.access_frequency > 0

    @pytest.mark.asyncio
    async def test_frequency_based_compaction(self):
        """Test frequency-based compaction strategy."""
        # Add entries with different access patterns
        for i in range(10):
            entry_id = f"entry_{i}"
            embedding = np.random.normal(0, 1, 128)
            await self.compactor.add_entry(entry_id, embedding, f"content_{i}")

            # Access some entries more frequently
            if i < 5:  # First 5 entries accessed more
                for _ in range(10):
                    await self.compactor.get_entry(entry_id)

        # Perform frequency-based compaction
        result = await self.compactor.compact(CompactionTrigger.MANUAL)

        assert result["status"] == "completed"
        assert result["entries_removed"] > 0
        assert result["memory_freed_mb"] > 0

    @pytest.mark.asyncio
    async def test_similarity_based_compaction(self):
        """Test similarity-based compaction strategy."""
        # Add highly similar entries
        base_embedding = np.random.normal(0, 1, 128)

        for i in range(10):
            # Create similar embeddings
            similar_embedding = base_embedding + np.random.normal(0, 0.01, 128)
            await self.compactor.add_entry(f"similar_{i}", similar_embedding, f"content_{i}")

        # Perform similarity-based compaction
        with patch.object(self.compactor.config, "primary_strategy", CompactionStrategy.SIMILARITY_BASED):
            result = await self.compactor.compact(CompactionTrigger.MANUAL)

        assert result["status"] == "completed"
        assert result["entries_removed"] > 0

    @pytest.mark.asyncio
    async def test_quality_based_compaction(self):
        """Test quality-based compaction strategy."""
        # Add entries with different quality scores
        for i in range(10):
            embedding = np.random.normal(0, 1, 128)
            await self.compactor.add_entry(f"entry_{i}", embedding, f"content_{i}")

            # Set quality scores
            entry = await self.compactor.get_entry(f"entry_{i}")
            entry.quality_score = 0.3 if i < 5 else 0.8  # First 5 have low quality

        # Perform quality-based compaction
        result = await self.compactor.optimize_quality(min_quality_threshold=0.5)

        assert result["status"] == "completed"
        assert result["entries_removed"] > 0

    def test_memory_statistics(self):
        """Test memory statistics functionality."""
        stats = self.compactor.get_memory_stats()

        assert "total_entries" in stats
        assert "total_memory_mb" in stats
        assert "average_access_count" in stats
        assert "average_quality_score" in stats
        assert "compaction_metrics" in stats

    @pytest.mark.asyncio
    async def test_compaction_metrics(self):
        """Test compaction metrics tracking."""
        # Add some entries
        for i in range(5):
            embedding = np.random.normal(0, 1, 128)
            await self.compactor.add_entry(f"entry_{i}", embedding, f"content_{i}")

        # Perform compaction
        await self.compactor.compact(CompactionTrigger.MANUAL)

        metrics = self.compactor.metrics
        assert metrics.total_compactions > 0
        assert metrics.total_entries_removed > 0
        assert metrics.total_memory_freed_mb > 0


class TestCrossTenantSimilarityDetector:
    """Test cross-tenant similarity detector functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = CrossTenantConfig(similarity_threshold=0.8, enable_caching=True)
        self.detector = CrossTenantSimilarityDetector(self.config)

    @pytest.mark.asyncio
    async def test_tenant_content_addition(self):
        """Test adding content for different tenants."""
        tenant1 = "tenant_1"
        tenant2 = "tenant_2"

        # Add content for tenant 1
        embedding1 = np.random.normal(0, 1, 128)
        result1 = await self.detector.add_tenant_content(tenant1, "content_1", embedding1, "content data 1")
        assert result1 is True

        # Add different content for tenant 2
        embedding2 = np.random.normal(0, 1, 128)
        result2 = await self.detector.add_tenant_content(tenant2, "content_2", embedding2, "content data 2")
        assert result2 is True

    @pytest.mark.asyncio
    async def test_cross_tenant_similarity_detection(self):
        """Test detection of cross-tenant similarity."""
        tenant1 = "tenant_1"
        tenant2 = "tenant_2"

        # Add similar content for both tenants
        base_embedding = np.random.normal(0, 1, 128)
        similar_embedding = base_embedding + np.random.normal(0, 0.01, 128)

        # Add to tenant 1
        result1 = await self.detector.add_tenant_content(tenant1, "content_1", base_embedding, "similar content")
        assert result1 is True

        # Try to add similar content to tenant 2
        result2 = await self.detector.add_tenant_content(tenant2, "content_2", similar_embedding, "similar content")
        # Should be blocked due to similarity
        assert result2 is False

    @pytest.mark.asyncio
    async def test_namespace_isolation(self):
        """Test namespace isolation strategy."""
        config = CrossTenantConfig(
            primary_strategy=IsolationStrategy.NAMESPACE_ISOLATION, enable_namespace_isolation=True
        )
        detector = CrossTenantSimilarityDetector(config)

        tenant_id = "test_tenant"
        embedding = np.random.normal(0, 1, 128)

        result = await detector.add_tenant_content(tenant_id, "content_1", embedding, "test content")

        assert result is True
        assert tenant_id in detector.tenant_namespaces

    @pytest.mark.asyncio
    async def test_embedding_perturbation(self):
        """Test embedding perturbation strategy."""
        config = CrossTenantConfig(
            primary_strategy=IsolationStrategy.EMBEDDING_PERTURBATION, perturbation_noise_level=0.1
        )
        detector = CrossTenantSimilarityDetector(config)

        tenant_id = "test_tenant"
        original_embedding = np.random.normal(0, 1, 128)

        result = await detector.add_tenant_content(tenant_id, "content_1", original_embedding, "test content")

        assert result is True

        # Check that embedding was perturbed
        stored_embedding = detector.tenant_embeddings[tenant_id]["content_1"]
        assert not np.array_equal(original_embedding, stored_embedding)

    @pytest.mark.asyncio
    async def test_similarity_violation_recording(self):
        """Test similarity violation recording."""
        tenant1 = "tenant_1"
        tenant2 = "tenant_2"

        # Add highly similar content
        base_embedding = np.random.normal(0, 1, 128)
        similar_embedding = base_embedding + np.random.normal(0, 0.001, 128)  # Very similar

        await self.detector.add_tenant_content(tenant1, "content_1", base_embedding, "content")

        # Check for violation
        violation = await self.detector.check_cross_tenant_similarity(tenant2, similar_embedding, "similar content")

        assert violation is not None
        assert violation.tenant1 == tenant2
        assert violation.tenant2 == tenant1
        assert violation.similarity_score > 0.8

    def test_tenant_isolation_statistics(self):
        """Test tenant isolation statistics."""
        stats = self.detector.get_tenant_isolation_stats()

        assert "total_tenants" in stats
        assert "total_content_items" in stats
        assert "total_violations" in stats
        assert "blocked_operations" in stats
        assert "average_check_time" in stats
        assert "cache_hit_rate" in stats
        assert "isolation_effectiveness" in stats

    @pytest.mark.asyncio
    async def test_tenant_data_cleanup(self):
        """Test tenant data cleanup functionality."""
        tenant_id = "test_tenant"

        # Add some data
        embedding = np.random.normal(0, 1, 128)
        await self.detector.add_tenant_content(tenant_id, "content_1", embedding, "content")

        # Cleanup
        result = await self.detector.cleanup_tenant_data(tenant_id)

        assert result["tenant_id"] == tenant_id
        assert result["embeddings_removed"] > 0
        assert result["content_removed"] > 0

        # Verify cleanup
        assert tenant_id not in self.detector.tenant_embeddings
        assert tenant_id not in self.detector.tenant_content

    def test_similarity_calculation_methods(self):
        """Test different similarity calculation methods."""
        embedding1 = np.random.normal(0, 1, 128)
        embedding2 = embedding1 + np.random.normal(0, 0.1, 128)

        # Test cosine similarity
        cosine_sim = self.detector._cosine_similarity(embedding1, embedding2)
        assert 0.0 <= cosine_sim <= 1.0

        # Test Euclidean similarity
        euclidean_sim = self.detector._euclidean_similarity(embedding1, embedding2)
        assert 0.0 <= euclidean_sim <= 1.0

        # Test embedding similarity
        embedding_sim = self.detector._embedding_similarity(embedding1, embedding2)
        assert 0.0 <= embedding_sim <= 1.0


class TestEnhancedMemoryIntegration:
    """Test integration of enhanced memory systems."""

    @pytest.mark.asyncio
    async def test_multimodal_with_compaction(self):
        """Test multi-modal embeddings with memory compaction."""
        # Create embedding generator
        generator = MultiModalEmbeddingGenerator()

        # Create compactor
        compactor = AdvancedMemoryCompactor()

        # Generate embeddings and add to compactor
        for i in range(5):
            text = f"Test content {i}"
            result = await generator.generate_text_embedding(text)

            await compactor.add_entry(f"entry_{i}", result.embedding, text, {"embedding_type": "text"})

        # Perform compaction
        compaction_result = await compactor.compact()

        assert compaction_result["status"] == "completed"
        assert len(compactor.entries) < 5  # Some entries should be removed

    @pytest.mark.asyncio
    async def test_cross_tenant_with_multimodal(self):
        """Test cross-tenant detection with multi-modal embeddings."""
        # Create systems
        generator = MultiModalEmbeddingGenerator()
        detector = CrossTenantSimilarityDetector()

        # Generate embeddings for different tenants
        tenant1 = "tenant_1"
        tenant2 = "tenant_2"

        text1 = "This is confidential information"
        text2 = "This is confidential information"  # Same text

        # Generate embeddings
        result1 = await generator.generate_text_embedding(text1)
        result2 = await generator.generate_text_embedding(text2)

        # Add to tenants
        success1 = await detector.add_tenant_content(tenant1, "content_1", result1.embedding, text1)
        assert success1 is True

        success2 = await detector.add_tenant_content(tenant2, "content_2", result2.embedding, text2)
        # Should be blocked due to similarity
        assert success2 is False

    @pytest.mark.asyncio
    async def test_full_memory_pipeline(self):
        """Test complete memory pipeline integration."""
        # Create all systems
        generator = MultiModalEmbeddingGenerator()
        compactor = AdvancedMemoryCompactor()
        detector = CrossTenantSimilarityDetector()

        # Process content for multiple tenants
        tenants = ["tenant_a", "tenant_b", "tenant_c"]
        content_items = []

        for tenant in tenants:
            for i in range(3):
                text = f"Content {i} for {tenant}"
                embedding_result = await generator.generate_text_embedding(text)

                # Check for cross-tenant similarity
                success = await detector.add_tenant_content(tenant, f"content_{i}", embedding_result.embedding, text)

                if success:
                    # Add to compactor
                    await compactor.add_entry(
                        f"{tenant}_content_{i}", embedding_result.embedding, text, {"tenant": tenant}
                    )
                    content_items.append((tenant, i, text))

        # Perform compaction
        compaction_result = await compactor.compact()

        # Verify results
        assert compaction_result["status"] == "completed"
        assert len(compactor.entries) > 0  # Some entries should remain
        assert detector.metrics.total_checks > 0


if __name__ == "__main__":
    pytest.main([__file__])
