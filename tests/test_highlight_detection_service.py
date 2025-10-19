"""Tests for Highlight Detection Service."""

from __future__ import annotations

import pytest

from analysis.highlight.highlight_detection_service import (
    HighlightDetectionService,
    HighlightSegment,
    get_highlight_detection_service,
)


class TestHighlightDetectionService:
    """Test highlight detection service functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = HighlightDetectionService(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.service.cache_size == 100
        assert len(self.service._detection_cache) == 0
        assert self.service._signal_weights["audio_energy"] == 0.4
        assert self.service._signal_weights["chat_spikes"] == 0.3
        assert self.service._signal_weights["semantic_novelty"] == 0.3

    def test_detect_highlights_fallback(self) -> None:
        """Test highlight detection with fallback method."""
        # Test without audio or transcript data
        result = self.service.detect_highlights(
            audio_path=None,
            transcript_segments=None,
            model="fast",
            use_cache=False,
        )

        # Should fail gracefully
        assert not result.success
        assert result.status == "bad_request"
        assert "must be provided" in result.error.lower()

    def test_detect_highlights_with_transcript(self) -> None:
        """Test highlight detection with transcript segments."""
        transcript_segments = [
            {"start_time": 0.0, "end_time": 10.0, "text": "Introduction"},
            {"start_time": 10.0, "end_time": 20.0, "text": "Main discussion"},
            {"start_time": 20.0, "end_time": 30.0, "text": "Conclusion"},
        ]

        result = self.service.detect_highlights(
            transcript_segments=transcript_segments,
            model="fast",
            use_cache=False,
        )

        # Should succeed with fallback method
        assert result.success
        assert result.data is not None
        assert "highlights" in result.data
        assert "total_duration" in result.data

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some cached detections
        self.service.detect_highlights(transcript_segments=[{"text": "test"}], use_cache=True)
        self.service.detect_highlights(transcript_segments=[{"text": "test2"}], use_cache=True)

        assert len(self.service._detection_cache) > 0

        # Clear cache
        result = self.service.clear_cache()

        assert result.success
        assert result.data["cleared_entries"] > 0
        assert len(self.service._detection_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        # Add some cached detections
        self.service.detect_highlights(transcript_segments=[{"text": "test"}], model="fast", use_cache=True)
        self.service.detect_highlights(transcript_segments=[{"text": "test2"}], model="balanced", use_cache=True)

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
        assert self.service._select_model("fast") == "fast_detection"
        assert self.service._select_model("balanced") == "balanced_detection"
        assert self.service._select_model("quality") == "quality_detection"
        assert self.service._select_model("unknown") == "balanced_detection"  # Default

    def test_signal_combination(self) -> None:
        """Test signal combination logic."""
        audio_scores = [0.8, 0.6, 0.9]
        chat_scores = [0.7, 0.5, 0.8]
        semantic_scores = [0.6, 0.8, 0.7]
        duration = 30.0

        combined = self.service._combine_signals(audio_scores, chat_scores, semantic_scores, duration)

        assert len(combined) == 3
        assert all(0 <= score <= 1 for score in combined)

    def test_highlight_segment_detection(self) -> None:
        """Test highlight segment detection."""
        scores = [0.3, 0.8, 0.9, 0.4, 0.7, 0.5]  # 6 segments

        highlights = self.service._detect_highlight_segments(scores, min_duration=10.0)

        assert len(highlights) >= 1
        # Should detect highlights where scores > 0.6
        assert highlights[0].highlight_score > 0.6

    def test_total_duration_calculation(self) -> None:
        """Test total duration calculation."""
        transcript_segments = [
            {"start_time": 0.0, "end_time": 10.0, "text": "Segment 1"},
            {"start_time": 10.0, "end_time": 25.0, "text": "Segment 2"},
        ]

        duration = self.service._get_total_duration(None, transcript_segments)

        assert duration == 55.0  # 25 + 30 buffer


class TestHighlightDetectionServiceSingleton:
    """Test singleton instance management."""

    def test_get_highlight_detection_service(self) -> None:
        """Test getting singleton instance."""
        service1 = get_highlight_detection_service()
        service2 = get_highlight_detection_service()

        # Should return same instance
        assert service1 is service2
        assert isinstance(service1, HighlightDetectionService)


class TestHighlightSegment:
    """Test highlight segment data structure."""

    def test_create_highlight_segment(self) -> None:
        """Test creating highlight segment."""
        highlight = HighlightSegment(
            start_time=10.0,
            end_time=25.0,
            duration=15.0,
            highlight_score=0.85,
            confidence=0.9,
            audio_energy_score=0.8,
            chat_spike_score=0.7,
            semantic_novelty_score=0.6,
            transcript_text="This is an exciting moment",
            speakers=["Host", "Guest"],
            topics=["technology", "AI"],
            highlight_type="debate",
        )

        assert highlight.start_time == 10.0
        assert highlight.end_time == 25.0
        assert highlight.duration == 15.0
        assert highlight.highlight_score == 0.85
        assert highlight.confidence == 0.9
        assert highlight.audio_energy_score == 0.8
        assert highlight.chat_spike_score == 0.7
        assert highlight.semantic_novelty_score == 0.6
        assert highlight.transcript_text == "This is an exciting moment"
        assert highlight.speakers == ["Host", "Guest"]
        assert highlight.topics == ["technology", "AI"]
        assert highlight.highlight_type == "debate"

    def test_highlight_segment_defaults(self) -> None:
        """Test highlight segment with default values."""
        highlight = HighlightSegment(
            start_time=0.0,
            end_time=10.0,
            duration=10.0,
            highlight_score=0.7,
            confidence=0.8,
        )

        assert highlight.audio_energy_score == 0.0
        assert highlight.chat_spike_score == 0.0
        assert highlight.semantic_novelty_score == 0.0
        assert highlight.transcript_text is None
        assert highlight.speakers is None
        assert highlight.topics is None
        assert highlight.highlight_type == "general"


class TestHighlightDetectionWithMocking:
    """Test highlight detection service with mocked dependencies."""

    def test_detect_highlights_with_audio_mock(self) -> None:
        """Test highlight detection with audio analysis."""
        # Mock librosa functions
        with pytest.importorskip("unittest.mock").patch(
            "analysis.highlight.highlight_detection_service.LIBROSA_AVAILABLE", True
        ):
            with pytest.importorskip("unittest.mock").patch("librosa.load") as mock_load:
                with pytest.importorskip("unittest.mock").patch("librosa.feature.rms") as mock_rms:
                    # Mock audio loading
                    mock_load.return_value = (pytest.importorskip("numpy").array([0.1, 0.2, 0.3]), 44100)

                    # Mock RMS calculation
                    mock_rms.return_value = pytest.importorskip("numpy").array([[0.8, 0.6, 0.9]])

                    service = HighlightDetectionService()

                    # Create dummy audio file
                    import tempfile
                    from pathlib import Path

                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        f.write(b"audio")
                        audio_path = Path(f.name)

                    try:
                        result = service.detect_highlights(
                            audio_path=audio_path,
                            model="balanced",
                            use_cache=False,
                        )

                        assert result.success
                        assert result.data["highlights"]

                    finally:
                        audio_path.unlink()

    def test_detect_highlights_with_chat_data(self) -> None:
        """Test highlight detection with chat spike analysis."""
        chat_data = [
            {"timestamp": 5.0, "message": "Great point!"},
            {"timestamp": 6.0, "message": "I agree!"},
            {"timestamp": 7.0, "message": "Amazing discussion!"},
            {"timestamp": 45.0, "message": "Question for the guest"},
        ]

        transcript_segments = [
            {"start_time": 0.0, "end_time": 30.0, "text": "Introduction"},
            {"start_time": 30.0, "end_time": 60.0, "text": "Main discussion"},
        ]

        result = self.service.detect_highlights(
            transcript_segments=transcript_segments,
            chat_data=chat_data,
            model="fast",
            use_cache=False,
        )

        assert result.success
        assert result.data["highlights"]

        # Should detect chat spike around 5-7 seconds
        highlights = result.data["highlights"]
        if highlights:
            # Check if any highlight covers the chat spike period
            chat_spike_highlight = any(h["start_time"] <= 7.0 <= h["end_time"] for h in highlights)
            assert chat_spike_highlight, "Should detect highlight around chat spike"


class TestHighlightDetectionEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = HighlightDetectionService()

    def test_detect_highlights_empty_inputs(self) -> None:
        """Test handling of empty inputs."""
        result = self.service.detect_highlights(
            transcript_segments=[],
            model="fast",
        )

        # Should handle gracefully
        assert result.success or result.status == "bad_request"

    def test_filter_and_rank_highlights(self) -> None:
        """Test highlight filtering and ranking."""
        highlights = [
            HighlightSegment(0, 10, 10, 0.9, 0.9),  # High score, good duration
            HighlightSegment(20, 25, 5, 0.8, 0.8),  # High score, short duration
            HighlightSegment(30, 45, 15, 0.6, 0.6),  # Medium score, good duration
            HighlightSegment(50, 55, 5, 0.4, 0.4),  # Low score, short duration
        ]

        filtered = self.service._filter_and_rank_highlights(highlights, max_highlights=3, min_duration=8.0)

        assert len(filtered) <= 3
        # Should be sorted by score
        assert filtered[0].highlight_score >= filtered[-1].highlight_score

    def test_signal_weights_modification(self) -> None:
        """Test signal weight modification."""
        # Modify weights
        self.service._signal_weights["audio_energy"] = 0.5
        self.service._signal_weights["chat_spikes"] = 0.3
        self.service._signal_weights["semantic_novelty"] = 0.2

        assert self.service._signal_weights["audio_energy"] == 0.5
        assert sum(self.service._signal_weights.values()) == 1.0
