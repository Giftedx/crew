"""Tests for EnhancedTranscriptionCache."""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from ultimate_discord_intelligence_bot.cache.enhanced_transcription_cache import EnhancedTranscriptionCache


class TestEnhancedTranscriptionCache:
    """Test suite for EnhancedTranscriptionCache."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = EnhancedTranscriptionCache(
            root=Path(self.temp_dir),
            enabled=True,
            compression_enabled=False,  # Disable for easier testing
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_initialization(self):
        """Test cache initialization."""
        assert self.cache.enabled
        assert self.cache.name == "transcription_cache"
        assert self.cache.size() == 0

    def test_cache_disabled(self):
        """Test cache when disabled."""
        disabled_cache = EnhancedTranscriptionCache(enabled=False)
        assert not disabled_cache.enabled

    def test_store_and_get_transcription(self):
        """Test storing and retrieving transcription."""
        video_id = "test_video_123"
        model_name = "test_model"
        transcript = "This is a test transcript"
        segments = [{"start": 0.0, "end": 5.0, "text": "This is a test"}]
        quality_score = 0.8

        # Store transcription
        success = self.cache.store_transcription(
            video_id=video_id,
            model_name=model_name,
            transcript=transcript,
            segments=segments,
            quality_score=quality_score,
        )
        assert success

        # Retrieve transcription
        result = self.cache.get_transcription(
            video_id=video_id,
            model_name=model_name,
        )
        assert result is not None
        assert result["transcript"] == transcript
        assert result["segments"] == segments
        assert result["quality_score"] == quality_score
        assert result["video_id"] == video_id
        assert result["model"] == model_name

    def test_cache_miss(self):
        """Test cache miss for non-existent entry."""
        result = self.cache.get_transcription(
            video_id="nonexistent",
            model_name="test_model",
        )
        assert result is None

    def test_cache_key_generation(self):
        """Test cache key generation with different parameters."""
        video_id = "test_video"
        model_name = "test_model"

        # Same parameters should generate same key
        key1 = self.cache._get_cache_path(video_id, model_name)
        key2 = self.cache._get_cache_path(video_id, model_name)
        assert key1 == key2

        # Different parameters should generate different keys
        key3 = self.cache._get_cache_path(video_id, "different_model")
        assert key1 != key3

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        # Create cache with very short TTL by patching config
        with patch(
            "ultimate_discord_intelligence_bot.cache.enhanced_transcription_cache.get_cache_config"
        ) as mock_config:
            mock_config.return_value.transcription.ttl_days = 0.00001  # Very short TTL
            mock_config.return_value.transcription.enabled = True
            mock_config.return_value.transcription.compression_enabled = False
            mock_config.return_value.transcription.cache_dir = self.temp_dir
            mock_config.return_value.global_enabled = True

            short_ttl_cache = EnhancedTranscriptionCache(
                root=Path(self.temp_dir),
                enabled=True,
            )

            video_id = "test_video"
            model_name = "test_model"
            transcript = "Test transcript"

            # Store transcription
            short_ttl_cache.store_transcription(
                video_id=video_id,
                model_name=model_name,
                transcript=transcript,
            )

            # Should be available immediately
            result = short_ttl_cache.get_transcription(video_id, model_name)
            assert result is not None

            # Wait for expiration
            time.sleep(1.1)

            # Should be expired now
            result = short_ttl_cache.get_transcription(video_id, model_name)
            assert result is None

    def test_delete_transcription(self):
        """Test deleting transcription."""
        video_id = "test_video"
        model_name = "test_model"
        transcript = "Test transcript"

        # Store transcription
        self.cache.store_transcription(
            video_id=video_id,
            model_name=model_name,
            transcript=transcript,
        )

        # Get the actual cache key used (full hash)
        from ultimate_discord_intelligence_bot.cache.cache_key_generator import generate_transcription_key

        key_name = generate_transcription_key(video_id, model_name)

        # Verify it exists
        assert self.cache.exists(key_name)

        # Delete it
        success = self.cache.delete(key_name)
        assert success

        # Verify it's gone
        assert not self.cache.exists(key_name)

    def test_clear_cache(self):
        """Test clearing all cache entries."""
        # Store multiple transcriptions
        for i in range(3):
            self.cache.store_transcription(
                video_id=f"video_{i}",
                model_name="test_model",
                transcript=f"Transcript {i}",
            )

        assert self.cache.size() == 3

        # Clear cache
        cleared_count = self.cache.clear()
        assert cleared_count == 3
        assert self.cache.size() == 0

    def test_metrics_tracking(self):
        """Test cache metrics tracking."""
        video_id = "test_video"
        model_name = "test_model"
        transcript = "Test transcript"

        # Initial metrics
        metrics = self.cache.get_metrics()
        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.stores == 0

        # Store transcription
        self.cache.store_transcription(
            video_id=video_id,
            model_name=model_name,
            transcript=transcript,
        )
        assert self.cache.get_metrics().stores == 1

        # Cache hit
        self.cache.get_transcription(video_id, model_name)
        assert self.cache.get_metrics().hits == 1

        # Cache miss
        self.cache.get_transcription("nonexistent", model_name)
        assert self.cache.get_metrics().misses == 1

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        # Create cache with very short TTL by patching config
        with patch(
            "ultimate_discord_intelligence_bot.cache.enhanced_transcription_cache.get_cache_config"
        ) as mock_config:
            mock_config.return_value.transcription.ttl_days = 0.00001  # Very short TTL (0.86 seconds)
            mock_config.return_value.transcription.enabled = True
            mock_config.return_value.transcription.compression_enabled = False
            mock_config.return_value.transcription.cache_dir = self.temp_dir
            mock_config.return_value.global_enabled = True

            short_ttl_cache = EnhancedTranscriptionCache(
                root=Path(self.temp_dir),
                enabled=True,
            )

            # Store multiple transcriptions
            for i in range(3):
                short_ttl_cache.store_transcription(
                    video_id=f"video_{i}",
                    model_name="test_model",
                    transcript=f"Transcript {i}",
                )

            assert short_ttl_cache.size() == 3

            # Wait for expiration
            time.sleep(1.0)

            # Cleanup expired entries
            cleaned_count = short_ttl_cache.cleanup_expired()
            assert cleaned_count == 3
            assert short_ttl_cache.size() == 0

    def test_empty_transcript_handling(self):
        """Test handling of empty transcript."""
        success = self.cache.store_transcription(
            video_id="test_video",
            model_name="test_model",
            transcript="",  # Empty transcript
        )
        assert not success

    def test_invalid_transcript_handling(self):
        """Test handling of invalid transcript data."""
        success = self.cache.store_transcription(
            video_id="test_video",
            model_name="test_model",
            transcript=None,  # Invalid transcript
        )
        assert not success

    def test_compression_enabled(self):
        """Test cache with compression enabled."""
        compressed_cache = EnhancedTranscriptionCache(
            root=Path(self.temp_dir),
            enabled=True,
            compression_enabled=True,
        )

        video_id = "test_video"
        model_name = "test_model"
        transcript = "This is a test transcript for compression testing"

        # Store and retrieve with compression
        success = compressed_cache.store_transcription(
            video_id=video_id,
            model_name=model_name,
            transcript=transcript,
        )
        assert success

        result = compressed_cache.get_transcription(video_id, model_name)
        assert result is not None
        assert result["transcript"] == transcript

    @patch("ultimate_discord_intelligence_bot.cache.enhanced_transcription_cache.get_cache_config")
    def test_configuration_integration(self, mock_get_config):
        """Test integration with configuration system."""
        mock_config = Mock()
        mock_config.global_enabled = True
        mock_config.transcription.enabled = True
        mock_config.transcription.ttl_days = 7
        mock_config.transcription.max_size_gb = 5
        mock_config.transcription.compression_enabled = True
        mock_config.transcription.cache_dir = "test_cache"
        mock_get_config.return_value = mock_config

        cache = EnhancedTranscriptionCache(enabled=True)
        assert cache.enabled
        assert cache.default_ttl_seconds == 7 * 24 * 3600
