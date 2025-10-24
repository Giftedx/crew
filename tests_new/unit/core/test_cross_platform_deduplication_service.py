"""Tests for Cross-Platform Deduplication Service."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from analysis.deduplication.cross_platform_deduplication_service import (
    CrossPlatformDeduplicationService,
    DuplicateCluster,
    get_cross_platform_deduplication_service,
)


class TestCrossPlatformDeduplicationService:
    """Test cross-platform deduplication service functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = CrossPlatformDeduplicationService(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.service.cache_size == 100
        assert len(self.service._deduplication_cache) == 0
        assert len(self.service._image_hashes) == 0
        assert len(self.service._text_hashes) == 0

    def test_find_duplicates_fallback(self) -> None:
        """Test deduplication with fallback method."""
        # Test without image or text data
        result = self.service.find_duplicates(
            image_paths=None,
            text_items=None,
            model="fast",
            use_cache=False,
        )

        # Should fail gracefully
        assert not result.success
        assert result.status == "bad_request"
        assert "must be provided" in result.error.lower()

    def test_find_duplicates_with_text_items(self) -> None:
        """Test deduplication with text items."""
        text_items = [
            {"id": "item1", "text": "This is a test text", "platform": "youtube"},
            {
                "id": "item2",
                "text": "This is a test text",
                "platform": "twitter",
            },  # Duplicate
            {"id": "item3", "text": "Different content", "platform": "reddit"},
        ]

        result = self.service.find_duplicates(
            text_items=text_items,
            similarity_threshold=0.9,
            model="fast",
            use_cache=False,
        )

        # Should succeed with text deduplication
        assert result.success
        assert result.data is not None
        assert "duplicate_clusters" in result.data
        assert result.data["total_items_processed"] == 3

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some cached deduplications
        self.service.find_duplicates(text_items=[{"text": "test"}], use_cache=True)
        self.service.find_duplicates(text_items=[{"text": "test2"}], use_cache=True)

        assert len(self.service._deduplication_cache) > 0

        # Clear cache
        result = self.service.clear_cache()

        assert result.success
        assert result.data["cleared_entries"] > 0
        assert len(self.service._deduplication_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        # Add some cached deduplications
        self.service.find_duplicates(text_items=[{"text": "test"}], model="fast", use_cache=True)
        self.service.find_duplicates(text_items=[{"text": "test2"}], model="balanced", use_cache=True)

        result = self.service.get_cache_stats()

        assert result.success
        assert result.data is not None
        assert "total_cached" in result.data
        assert "cache_size_limit" in result.data
        assert "models_cached" in result.data

        assert result.data["total_cached"] >= 2
        assert result.data["cache_size_limit"] == 100

    def test_model_selection(self) -> None:
        """Test model selection logic."""
        assert self.service._select_model("fast") == "fast_deduplication"
        assert self.service._select_model("balanced") == "balanced_deduplication"
        assert self.service._select_model("quality") == "quality_deduplication"
        assert self.service._select_model("unknown") == "balanced_deduplication"  # Default

    def test_deduplicate_content_stream(self) -> None:
        """Test real-time content stream deduplication."""
        content_items = [
            {"id": "item1", "content_type": "text", "text": "This is test content"},
            {
                "id": "item2",
                "content_type": "text",
                "text": "This is test content",
            },  # Duplicate
            {"id": "item3", "content_type": "text", "text": "Different content"},
        ]

        result = self.service.deduplicate_content_stream(content_items, similarity_threshold=0.9, model="fast")

        assert result.success
        assert result.data is not None
        assert "processed_items" in result.data
        assert result.data["total_items_processed"] == 3

        # Check that duplicates were marked
        processed_items = result.data["processed_items"]
        duplicates = [item for item in processed_items if item.get("is_duplicate")]
        assert len(duplicates) >= 1

    def test_text_similarity_calculation(self) -> None:
        """Test text similarity calculation."""
        text1 = "This is a test"
        text2 = "This is a test"  # Identical

        similarity = self.service._calculate_text_similarity(text1, text2)
        assert similarity == 1.0

        text3 = "Completely different content"
        similarity2 = self.service._calculate_text_similarity(text1, text3)
        assert similarity2 < 1.0

    def test_image_hash_generation_fallback(self) -> None:
        """Test image hash generation fallback."""
        # Test without imagehash available
        with patch(
            "analysis.deduplication.cross_platform_deduplication_service.IMAGEHASH_AVAILABLE",
            False,
        ):
            hash_value = self.service._get_image_hash("fake_path.jpg")
            assert isinstance(hash_value, str)
            assert len(hash_value) == 64  # SHA256 hex length


class TestCrossPlatformDeduplicationServiceSingleton:
    """Test singleton instance management."""

    def test_get_cross_platform_deduplication_service(self) -> None:
        """Test getting singleton instance."""
        service1 = get_cross_platform_deduplication_service()
        service2 = get_cross_platform_deduplication_service()

        # Should return same instance
        assert service1 is service2
        assert isinstance(service1, CrossPlatformDeduplicationService)


class TestDuplicateCluster:
    """Test duplicate cluster data structure."""

    def test_create_duplicate_cluster(self) -> None:
        """Test creating duplicate cluster."""
        cluster = DuplicateCluster(
            cluster_id="test_cluster",
            platform_items={
                "youtube": [{"id": "yt1", "title": "Video 1"}],
                "twitter": [{"id": "tw1", "text": "Tweet 1"}],
            },
            similarity_scores={"yt1": 0.95, "tw1": 0.90},
            representative_item={"id": "yt1", "title": "Video 1"},
            confidence=0.92,
        )

        assert cluster.cluster_id == "test_cluster"
        assert "youtube" in cluster.platform_items
        assert "twitter" in cluster.platform_items
        assert len(cluster.platform_items["youtube"]) == 1
        assert len(cluster.platform_items["twitter"]) == 1
        assert cluster.similarity_scores["yt1"] == 0.95
        assert cluster.representative_item["id"] == "yt1"
        assert cluster.confidence == 0.92

    def test_duplicate_cluster_empty(self) -> None:
        """Test duplicate cluster with no items."""
        cluster = DuplicateCluster(
            cluster_id="empty_cluster",
            platform_items={},
            similarity_scores={},
            representative_item={},
            confidence=0.0,
        )

        assert cluster.cluster_id == "empty_cluster"
        assert len(cluster.platform_items) == 0
        assert len(cluster.similarity_scores) == 0


class TestCrossPlatformDeduplicationWithMocking:
    """Test deduplication service with mocked dependencies."""

    def test_find_image_duplicates_with_hash_mock(self) -> None:
        """Test image deduplication with mocked hashing."""
        # Mock imagehash functions
        with (
            patch(
                "analysis.deduplication.cross_platform_deduplication_service.IMAGEHASH_AVAILABLE",
                True,
            ),
            patch("analysis.deduplication.cross_platform_deduplication_service.imagehash") as mock_imagehash,
        ):
            # Mock hash generation
            mock_hash = "8f8f8f8f8f8f8f8f"  # Mock hex hash
            mock_imagehash.average_hash.return_value = mock_hash
            mock_imagehash.hex_to_hash.return_value = mock_hash

            service = CrossPlatformDeduplicationService()

            # Create dummy image files
            image_paths = []
            for i in range(3):
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                    f.write(f"image content {i}".encode())
                    image_paths.append(f.name)

            try:
                result = service.find_duplicates(
                    image_paths=image_paths,
                    similarity_threshold=0.8,
                    model="balanced",
                    use_cache=False,
                )

                assert result.success
                assert result.data["total_items_processed"] == 3

            finally:
                for path in image_paths:
                    Path(path).unlink()

    def test_deduplicate_content_stream_with_mixed_types(self) -> None:
        """Test stream deduplication with mixed content types."""
        content_items = [
            {"id": "img1", "content_type": "image", "image_path": "image1.jpg"},
            {"id": "txt1", "content_type": "text", "text": "Test content"},
            {
                "id": "img2",
                "content_type": "image",
                "image_path": "image1.jpg",
            },  # Duplicate image
            {
                "id": "txt2",
                "content_type": "text",
                "text": "Test content",
            },  # Duplicate text
        ]

        result = self.service.deduplicate_content_stream(content_items, similarity_threshold=0.9, model="fast")

        assert result.success
        assert result.data["total_items_processed"] == 4

        # Should detect some duplicates
        processed_items = result.data["processed_items"]
        duplicates = [item for item in processed_items if item.get("is_duplicate")]
        assert len(duplicates) >= 2  # At least the two duplicates we created


class TestCrossPlatformDeduplicationEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = CrossPlatformDeduplicationService()

    def test_find_duplicates_empty_inputs(self) -> None:
        """Test handling of empty input lists."""
        result = self.service.find_duplicates(
            image_paths=[],
            text_items=[],
            model="fast",
        )

        # Should handle gracefully
        assert result.success or result.status == "bad_request"

    def test_text_hash_generation(self) -> None:
        """Test text hash generation."""
        text = "This is a test text for hashing"

        embedding = self.service._get_text_hash(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 768  # Sentence-transformer dimension
        assert all(isinstance(x, float) for x in embedding)
        assert all(-1.0 <= x <= 1.0 for x in embedding)

    def test_similarity_threshold_filtering(self) -> None:
        """Test that similarity threshold filtering works."""
        text_items = [
            {"id": "item1", "text": "This is a test"},
            {"id": "item2", "text": "This is a different test"},  # Low similarity
            {"id": "item3", "text": "This is a test"},  # High similarity to item1
        ]

        # High threshold should find fewer duplicates
        result_high = self.service.find_duplicates(
            text_items=text_items,
            similarity_threshold=0.95,
            model="fast",
            use_cache=False,
        )

        # Low threshold should find more duplicates
        result_low = self.service.find_duplicates(
            text_items=text_items,
            similarity_threshold=0.5,
            model="fast",
            use_cache=False,
        )

        assert result_high.success and result_low.success

        # High threshold should find fewer or equal duplicates
        high_duplicates = result_high.data.get("duplicates_found", 0)
        low_duplicates = result_low.data.get("duplicates_found", 0)

        assert high_duplicates <= low_duplicates
