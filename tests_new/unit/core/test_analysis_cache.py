"""Tests for AnalysisCache."""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from ultimate_discord_intelligence_bot.cache.analysis_cache import AnalysisCache


class TestAnalysisCache:
    """Test suite for AnalysisCache."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = AnalysisCache(
            root=Path(self.temp_dir),
            enabled=True,
            disk_persistence_enabled=False,  # Disable for easier testing
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_initialization(self):
        """Test cache initialization."""
        assert self.cache.enabled
        assert self.cache.name == "analysis_cache"
        assert self.cache.size() == 0

    def test_cache_disabled(self):
        """Test cache when disabled."""
        disabled_cache = AnalysisCache(enabled=False)
        assert not disabled_cache.enabled

    def test_store_and_get_analysis(self):
        """Test storing and retrieving analysis results."""
        transcript_hash = "abc123"
        depth = "deep"
        analysis_type = "text_analysis"
        analysis_results = {
            "sentiment": "positive",
            "themes": ["technology", "innovation"],
            "keywords": ["AI", "machine learning"],
        }
        confidence_scores = {"overall": 0.85, "sentiment": 0.9}
        metadata = {"model_version": "v1.2", "processing_time": 1.5}

        # Store analysis
        success = self.cache.store_analysis(
            transcript_hash=transcript_hash,
            depth=depth,
            analysis_type=analysis_type,
            analysis_results=analysis_results,
            confidence_scores=confidence_scores,
            metadata=metadata,
        )
        assert success

        # Retrieve analysis
        result = self.cache.get_analysis(
            transcript_hash=transcript_hash,
            depth=depth,
            analysis_type=analysis_type,
        )
        assert result is not None
        assert result["analysis_results"] == analysis_results
        assert result["confidence_scores"] == confidence_scores
        assert result["metadata"] == metadata
        assert result["transcript_hash"] == transcript_hash
        assert result["depth"] == depth
        assert result["analysis_type"] == analysis_type

    def test_cache_miss(self):
        """Test cache miss for non-existent entry."""
        result = self.cache.get_analysis(
            transcript_hash="nonexistent",
            depth="standard",
            analysis_type="text_analysis",
        )
        assert result is None

    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        # Create cache with small max entries
        small_cache = AnalysisCache(
            root=Path(self.temp_dir),
            enabled=True,
            disk_persistence_enabled=False,
        )
        small_cache._max_entries = 2  # Force small size

        # Store first entry
        small_cache.store_analysis(
            transcript_hash="hash1",
            depth="standard",
            analysis_type="text",
            analysis_results={"result": "first"},
        )

        # Store second entry
        small_cache.store_analysis(
            transcript_hash="hash2",
            depth="standard",
            analysis_type="text",
            analysis_results={"result": "second"},
        )

        assert small_cache.size() == 2

        # Store third entry (should evict first)
        small_cache.store_analysis(
            transcript_hash="hash3",
            depth="standard",
            analysis_type="text",
            analysis_results={"result": "third"},
        )

        assert small_cache.size() == 2

        # First entry should be evicted
        result1 = small_cache.get_analysis("hash1", "standard", "text")
        assert result1 is None

        # Second and third should still be available
        result2 = small_cache.get_analysis("hash2", "standard", "text")
        result3 = small_cache.get_analysis("hash3", "standard", "text")
        assert result2 is not None
        assert result3 is not None

    def test_lru_access_update(self):
        """Test that accessing an entry updates its LRU position."""
        # Create cache with small max entries
        small_cache = AnalysisCache(
            root=Path(self.temp_dir),
            enabled=True,
            disk_persistence_enabled=False,
        )
        small_cache._max_entries = 2

        # Store first entry
        small_cache.store_analysis(
            transcript_hash="hash1",
            depth="standard",
            analysis_type="text",
            analysis_results={"result": "first"},
        )

        # Store second entry
        small_cache.store_analysis(
            transcript_hash="hash2",
            depth="standard",
            analysis_type="text",
            analysis_results={"result": "second"},
        )

        # Access first entry (should move it to end)
        small_cache.get_analysis("hash1", "standard", "text")

        # Store third entry (should evict second, not first)
        small_cache.store_analysis(
            transcript_hash="hash3",
            depth="standard",
            analysis_type="text",
            analysis_results={"result": "third"},
        )

        # First and third should be available, second should be evicted
        result1 = small_cache.get_analysis("hash1", "standard", "text")
        result2 = small_cache.get_analysis("hash2", "standard", "text")
        result3 = small_cache.get_analysis("hash3", "standard", "text")

        assert result1 is not None
        assert result2 is None
        assert result3 is not None

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        # Create cache with very short TTL by patching config
        with patch("ultimate_discord_intelligence_bot.cache.analysis_cache.get_cache_config") as mock_config:
            mock_config.return_value.analysis.ttl_hours = 0.00001  # Very short TTL
            mock_config.return_value.analysis.enabled = True
            mock_config.return_value.analysis.disk_persistence_enabled = False
            mock_config.return_value.analysis.cache_dir = self.temp_dir
            mock_config.return_value.global_enabled = True

            short_ttl_cache = AnalysisCache(
                root=Path(self.temp_dir),
                enabled=True,
                disk_persistence_enabled=False,
            )

            transcript_hash = "test_hash"
            depth = "standard"
            analysis_type = "text"

            # Store analysis
            short_ttl_cache.store_analysis(
                transcript_hash=transcript_hash,
                depth=depth,
                analysis_type=analysis_type,
                analysis_results={"result": "test"},
            )

            # Should be available immediately
            result = short_ttl_cache.get_analysis(transcript_hash, depth, analysis_type)
            assert result is not None

            # Wait for expiration
            time.sleep(1.1)

            # Should be expired now
            result = short_ttl_cache.get_analysis(transcript_hash, depth, analysis_type)
            assert result is None

    def test_delete_analysis(self):
        """Test deleting analysis."""
        transcript_hash = "test_hash"
        depth = "standard"
        analysis_type = "text"
        analysis_results = {"result": "test"}

        # Store analysis
        self.cache.store_analysis(
            transcript_hash=transcript_hash,
            depth=depth,
            analysis_type=analysis_type,
            analysis_results=analysis_results,
        )

        # Get the actual key used by the cache
        from ultimate_discord_intelligence_bot.cache.cache_key_generator import (
            generate_analysis_key,
        )

        key = generate_analysis_key(transcript_hash, depth, analysis_type, "v1")

        # Verify it exists
        assert self.cache.exists(key)

        # Delete it
        success = self.cache.delete(key)
        assert success

        # Verify it's gone
        assert not self.cache.exists(key)

    def test_clear_cache(self):
        """Test clearing all cache entries."""
        # Store multiple analyses
        for i in range(3):
            self.cache.store_analysis(
                transcript_hash=f"hash_{i}",
                depth="standard",
                analysis_type="text",
                analysis_results={"result": f"analysis_{i}"},
            )

        assert self.cache.size() == 3

        # Clear cache
        cleared_count = self.cache.clear()
        assert cleared_count == 3
        assert self.cache.size() == 0

    def test_metrics_tracking(self):
        """Test cache metrics tracking."""
        transcript_hash = "test_hash"
        depth = "standard"
        analysis_type = "text"
        analysis_results = {"result": "test"}

        # Initial metrics
        metrics = self.cache.get_metrics()
        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.stores == 0

        # Store analysis
        self.cache.store_analysis(
            transcript_hash=transcript_hash,
            depth=depth,
            analysis_type=analysis_type,
            analysis_results=analysis_results,
        )
        assert self.cache.get_metrics().stores == 1

        # Cache hit
        self.cache.get_analysis(transcript_hash, depth, analysis_type)
        assert self.cache.get_metrics().hits == 1

        # Cache miss
        self.cache.get_analysis("nonexistent", depth, analysis_type)
        assert self.cache.get_metrics().misses == 1

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        # Create cache with very short TTL by patching config
        with patch("ultimate_discord_intelligence_bot.cache.analysis_cache.get_cache_config") as mock_config:
            mock_config.return_value.analysis.ttl_hours = 0.0001  # Very short TTL
            mock_config.return_value.analysis.enabled = True
            mock_config.return_value.analysis.disk_persistence_enabled = False
            mock_config.return_value.analysis.cache_dir = self.temp_dir
            mock_config.return_value.global_enabled = True

            short_ttl_cache = AnalysisCache(
                root=Path(self.temp_dir),
                enabled=True,
                disk_persistence_enabled=False,
            )

            # Store multiple analyses
            for i in range(3):
                short_ttl_cache.store_analysis(
                    transcript_hash=f"hash_{i}",
                    depth="standard",
                    analysis_type="text",
                    analysis_results={"result": f"analysis_{i}"},
                )

            assert short_ttl_cache.size() == 3

            # Wait for expiration
            time.sleep(1.0)

            # Cleanup expired entries
            cleaned_count = short_ttl_cache.cleanup_expired()
            assert cleaned_count == 3
            assert short_ttl_cache.size() == 0

    def test_empty_analysis_handling(self):
        """Test handling of empty analysis results."""
        success = self.cache.store_analysis(
            transcript_hash="test_hash",
            depth="standard",
            analysis_type="text",
            analysis_results={},  # Empty results
        )
        assert not success

    def test_invalid_analysis_handling(self):
        """Test handling of invalid analysis data."""
        success = self.cache.store_analysis(
            transcript_hash="test_hash",
            depth="standard",
            analysis_type="text",
            analysis_results=None,  # Invalid results
        )
        assert not success

    def test_disk_persistence(self):
        """Test disk persistence functionality."""
        persistent_cache = AnalysisCache(
            root=Path(self.temp_dir),
            enabled=True,
            disk_persistence_enabled=True,
        )

        transcript_hash = "persistent_hash"
        depth = "standard"
        analysis_type = "text"
        analysis_results = {"result": "persistent_test"}

        # Store analysis
        persistent_cache.store_analysis(
            transcript_hash=transcript_hash,
            depth=depth,
            analysis_type=analysis_type,
            analysis_results=analysis_results,
        )

        # Create new cache instance (simulating restart)
        new_cache = AnalysisCache(
            root=Path(self.temp_dir),
            enabled=True,
            disk_persistence_enabled=True,
        )

        # Should be able to load from disk
        result = new_cache.get_analysis(transcript_hash, depth, analysis_type)
        assert result is not None
        assert result["analysis_results"] == analysis_results

    def test_warm_up_from_history(self):
        """Test warming up cache from historical data."""
        history_data = [
            {
                "transcript_hash": "hist_hash1",
                "depth": "standard",
                "analysis_type": "text",
                "analysis_results": {"result": "history1"},
                "confidence_scores": {"overall": 0.8},
            },
            {
                "transcript_hash": "hist_hash2",
                "depth": "deep",
                "analysis_type": "fact_checking",
                "analysis_results": {"result": "history2"},
                "confidence_scores": {"overall": 0.9},
            },
            {
                "transcript_hash": "hist_hash3",
                "depth": "standard",
                "analysis_type": "text",
                # Missing required fields - should be skipped
                "analysis_results": None,
            },
        ]

        added_count = self.cache.warm_up_from_history(history_data)
        assert added_count == 2  # Only first two should be added
        assert self.cache.size() == 2

        # Verify first two entries are accessible
        result1 = self.cache.get_analysis("hist_hash1", "standard", "text")
        result2 = self.cache.get_analysis("hist_hash2", "deep", "fact_checking")
        assert result1 is not None
        assert result2 is not None

    @patch("ultimate_discord_intelligence_bot.cache.analysis_cache.get_cache_config")
    def test_configuration_integration(self, mock_get_config):
        """Test integration with configuration system."""
        mock_config = Mock()
        mock_config.global_enabled = True
        mock_config.analysis.enabled = True
        mock_config.analysis.ttl_hours = 24
        mock_config.analysis.max_entries = 50
        mock_config.analysis.disk_persistence_enabled = True
        mock_config.analysis.cache_dir = "test_cache"
        mock_get_config.return_value = mock_config

        cache = AnalysisCache(enabled=True)
        assert cache.enabled
        assert cache.default_ttl_seconds == 24 * 3600
        assert cache._max_entries == 50
