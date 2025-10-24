"""Tests for ASR (Automatic Speech Recognition) Service."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from analysis.transcription.asr_service import ASRService, get_asr_service


class TestASRService:
    """Test ASR service functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = ASRService(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.service.cache_size == 100
        assert len(self.service._transcription_cache) == 0
        assert len(self.service._models) == 0

    def test_transcribe_fallback(self) -> None:
        """Test transcription with fallback model."""
        # Create a dummy audio file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"dummy audio content")
            audio_path = Path(f.name)

        try:
            result = self.service.transcribe_audio(audio_path, model="fast", use_cache=False)

            assert result.success
            assert result.data is not None
            assert "text" in result.data
            assert "segments" in result.data
            assert "model" in result.data
            assert "cache_hit" in result.data

            # Fallback should return low confidence
            assert result.data["confidence"] == 0.5
            assert "fallback" in result.data["model"]

        finally:
            audio_path.unlink()

    def test_transcribe_empty_file(self) -> None:
        """Test handling of empty audio file."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            audio_path = Path(f.name)

        try:
            result = self.service.transcribe_audio(audio_path, model="fast")

            assert not result.success
            assert result.status == "bad_request"
            assert "empty" in result.error.lower()

        finally:
            audio_path.unlink()

    def test_transcribe_nonexistent_file(self) -> None:
        """Test handling of non-existent file."""
        result = self.service.transcribe_audio("nonexistent.mp3", model="fast")

        assert not result.success
        assert result.status == "bad_request"
        assert "not found" in result.error.lower()

    def test_transcription_cache_hit(self) -> None:
        """Test transcription cache functionality."""
        # Create a dummy audio file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"test audio content")
            audio_path = Path(f.name)

        try:
            # First transcription - cache miss
            result1 = self.service.transcribe_audio(audio_path, model="fast", use_cache=True)
            assert result1.success
            assert result1.data["cache_hit"] is False

            # Second transcription - should be cache hit
            result2 = self.service.transcribe_audio(audio_path, model="fast", use_cache=True)
            assert result2.success
            assert result2.data["cache_hit"] is True

            # Results should be identical
            assert result1.data["text"] == result2.data["text"]

        finally:
            audio_path.unlink()

    def test_transcribe_batch(self) -> None:
        """Test batch transcription."""
        # Create multiple dummy audio files
        audio_paths = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(f"audio content {i}".encode())
                audio_paths.append(Path(f.name))

        try:
            result = self.service.transcribe_batch(audio_paths, model="fast", use_cache=False)

            assert result.success
            assert result.data is not None
            assert "results" in result.data
            assert len(result.data["results"]) == 3
            assert result.data["count"] == 3

        finally:
            for path in audio_paths:
                path.unlink()

    def test_transcribe_batch_empty_list(self) -> None:
        """Test batch transcription with empty list."""
        result = self.service.transcribe_batch([], model="fast")

        assert not result.success
        assert result.status == "bad_request"

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some cached transcriptions
        self.service.transcribe_audio("dummy1.mp3", use_cache=True)
        self.service.transcribe_audio("dummy2.mp3", use_cache=True)

        assert len(self.service._transcription_cache) > 0

        # Clear cache
        result = self.service.clear_cache()

        assert result.success
        assert result.data["cleared_entries"] > 0
        assert len(self.service._transcription_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        # Add some cached transcriptions
        self.service.transcribe_audio("dummy1.mp3", model="fast", use_cache=True)
        self.service.transcribe_audio("dummy2.mp3", model="balanced", use_cache=True)

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
        assert self.service._select_model("fast") == "faster-whisper-tiny"
        assert self.service._select_model("balanced") == "faster-whisper-base"
        assert self.service._select_model("quality") == "openai-whisper-large-v3"
        assert self.service._select_model("unknown") == "faster-whisper-base"  # Default

    def test_cache_eviction(self) -> None:
        """Test cache eviction when full."""
        # Create service with small cache
        service = ASRService(cache_size=2)

        # Fill cache beyond capacity
        service.transcribe_audio("dummy1.mp3", use_cache=True)
        service.transcribe_audio("dummy2.mp3", use_cache=True)
        service.transcribe_audio("dummy3.mp3", use_cache=True)  # Should trigger eviction

        # Cache should not exceed limit
        assert len(service._transcription_cache) <= 2

    def test_cache_bypass(self) -> None:
        """Test bypassing cache."""
        # Create a dummy audio file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"test content")
            audio_path = Path(f.name)

        try:
            # First call with cache
            result1 = self.service.transcribe_audio(audio_path, use_cache=True)
            assert result1.success

            # Second call bypassing cache
            result2 = self.service.transcribe_audio(audio_path, use_cache=False)
            assert result2.success
            assert result2.data["cache_hit"] is False

        finally:
            audio_path.unlink()


class TestASRServiceSingleton:
    """Test singleton instance management."""

    def test_get_asr_service(self) -> None:
        """Test getting singleton instance."""
        service1 = get_asr_service()
        service2 = get_asr_service()

        # Should return same instance
        assert service1 is service2
        assert isinstance(service1, ASRService)


class TestASRServiceWithMocking:
    """Test ASR service with mocked dependencies."""

    @patch("faster_whisper.WhisperModel")
    def test_transcribe_local_model(self, mock_whisper_model):
        """Test transcription with local Whisper model."""
        # Mock Whisper model
        mock_model = MagicMock()
        mock_whisper_model.return_value = mock_model

        # Mock transcription response
        mock_segments = [
            MagicMock(start=0.0, end=1.0, text="Hello world", probability=0.95),
            MagicMock(start=1.0, end=2.0, text="This is a test", probability=0.90),
        ]
        mock_info = MagicMock(duration=2.0, language="en")

        mock_model.transcribe.return_value = (mock_segments, mock_info)

        # Create service with mocked availability
        with patch("analysis.transcription.asr_service.FASTER_WHISPER_AVAILABLE", True):
            service = ASRService()

            # Create dummy audio file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(b"audio")
                audio_path = Path(f.name)

            try:
                result = service.transcribe_audio(audio_path, model="fast", use_cache=False)

                assert result.success
                assert result.data["text"] == "Hello world This is a test"
                assert len(result.data["segments"]) == 2
                assert result.data["model"] == "faster-whisper-tiny"
                assert result.data["duration"] == 2.0
                assert result.data["language"] == "en"

                # Verify Whisper model was called
                mock_model.transcribe.assert_called_once()

            finally:
                audio_path.unlink()

    @patch("openai.OpenAI")
    def test_transcribe_openai_model(self, mock_openai_client):
        """Test transcription with OpenAI API."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.text = "OpenAI transcribed text"
        mock_response.segments = [
            MagicMock(start=0.0, end=1.0, text="OpenAI", confidence=0.95),
        ]
        mock_response.duration = 1.0
        mock_response.language = "en"
        mock_response.confidence = 0.95
        mock_response.usage = MagicMock(total_tokens=10)

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client

        # Create service with mocked availability
        with patch("analysis.transcription.asr_service.OPENAI_AVAILABLE", True):
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                service = ASRService()

                # Create dummy audio file
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    f.write(b"audio")
                    audio_path = Path(f.name)

                try:
                    result = service.transcribe_audio(audio_path, model="quality", use_cache=False)

                    assert result.success
                    assert result.data["text"] == "OpenAI transcribed text"
                    assert len(result.data["segments"]) == 1
                    assert result.data["model"] == "openai-whisper-large-v3"
                    assert result.data["tokens_used"] == 10

                    # Verify OpenAI API was called
                    mock_client.audio.transcriptions.create.assert_called_once()

                finally:
                    audio_path.unlink()
