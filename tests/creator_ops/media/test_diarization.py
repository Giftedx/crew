"""
Unit tests for Speaker Diarization functionality.

Tests cover:
- pyannote.audio model initialization and configuration
- Audio file processing and speaker identification
- Speaker change detection and segmentation
- Performance metrics (DER <15% target)
- Error handling and edge cases
- Overlap handling and speaker count estimation
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ultimate_discord_intelligence_bot.creator_ops.media.diarization import (
    DiarizationResult,
    DiarizationSegment,
    SpeakerDiarization,
)


class TestSpeakerDiarization:
    """Test suite for speaker diarization functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = SpeakerDiarization(
            model_name="pyannote/speaker-diarization-3.1",
            device="cpu",
        )

    def test_initialization(self):
        """Test speaker diarization initialization."""
        assert self.processor.model_name == "pyannote/speaker-diarization-3.1"
        assert self.processor.device == "cpu"
        assert self.processor.pipeline is None  # Not loaded until first use

    @patch("pyannote.audio.Pipeline.from_pretrained")
    def test_pipeline_initialization_success(self, mock_pipeline):
        """Test successful pipeline initialization."""
        mock_model = Mock()
        mock_pipeline.return_value = mock_model

        # Re-initialize to test pipeline loading
        processor = SpeakerDiarization(
            model_name="pyannote/speaker-diarization-3.1",
            device="cpu",
        )

        assert processor.pipeline == mock_model
        mock_pipeline.assert_called_once_with(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=None,
        )

    @patch("pyannote.audio.Pipeline.from_pretrained")
    def test_pipeline_initialization_failure(self, mock_pipeline):
        """Test pipeline initialization failure."""
        mock_pipeline.side_effect = Exception("Pipeline loading failed")

        with pytest.raises(Exception, match="Pipeline loading failed"):
            SpeakerDiarization(
                model_name="pyannote/speaker-diarization-3.1",
                device="cpu",
            )

    def test_get_optimal_device_cpu(self):
        """Test device selection for CPU."""
        processor = SpeakerDiarization(device="cpu")
        assert processor.device == "cpu"

    @patch("torch.cuda.is_available", return_value=False)
    def test_get_optimal_device_no_gpu(self, mock_cuda):
        """Test device selection when GPU is not available."""
        processor = SpeakerDiarization()
        assert processor.device == "cpu"

    @patch("pyannote.audio.Pipeline.from_pretrained")
    def test_diarize_audio_success(self, mock_pipeline):
        """Test successful audio diarization."""
        # Mock model and diarization result
        mock_model = Mock()
        mock_pipeline.return_value = mock_model

        # Mock diarization result with speaker segments
        mock_diarization_result = Mock()
        mock_diarization_result.itertracks = Mock(
            return_value=[
                (Mock(start=0.0, end=2.5), None, "SPEAKER_00"),
                (Mock(start=2.5, end=5.0), None, "SPEAKER_01"),
                (Mock(start=5.0, end=7.5), None, "SPEAKER_00"),
            ]
        )

        mock_model.return_value = mock_diarization_result

        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
            audio_file.write(b"fake_audio_data")
            audio_file_path = audio_file.name

        try:
            result = self.processor.diarize_audio(audio_file_path)

            assert result.success
            assert "data" in result.data
            diarization_result = result.data["data"]
            assert isinstance(diarization_result, DiarizationResult)
            assert len(diarization_result.segments) == 3
            assert diarization_result.speaker_count == 2
            assert diarization_result.duration == 7.5

            # Check first segment
            first_segment = diarization_result.segments[0]
            assert first_segment.speaker == "SPEAKER_00"
            assert first_segment.start_time == 0.0
            assert first_segment.end_time == 2.5

        finally:
            Path(audio_file_path).unlink()

    def test_diarize_audio_empty_path(self):
        """Test diarization with empty audio path."""
        result = self.processor.diarize_audio("")

        assert not result.success
        assert "Audio path cannot be empty" in result.error

    @patch("pyannote.audio.Pipeline.from_pretrained")
    def test_diarize_audio_diarization_error(self, mock_pipeline):
        """Test diarization with model error."""
        mock_model = Mock()
        mock_pipeline.return_value = mock_model
        mock_model.side_effect = Exception("Diarization failed")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
            audio_file.write(b"fake_audio_data")
            audio_file_path = audio_file.name

        try:
            result = self.processor.diarize_audio(audio_file_path)

            assert not result.success
            assert "Speaker diarization failed" in result.error

        finally:
            Path(audio_file_path).unlink()

    @patch("pyannote.metrics.diarization.DiarizationErrorRate")
    def test_evaluate_der_success(self, mock_der_class):
        """Test Diarization Error Rate evaluation."""
        # Mock DER calculator
        mock_der = Mock()
        mock_der_class.return_value = mock_der
        mock_der.return_value = 0.05  # 5% error rate

        # Create reference and predicted results
        reference_segments = [
            DiarizationSegment(0.0, 2.0, "SPEAKER_00"),
            DiarizationSegment(2.0, 4.0, "SPEAKER_01"),
            DiarizationSegment(4.0, 6.0, "SPEAKER_00"),
        ]

        predicted_segments = [
            DiarizationSegment(0.0, 2.1, "SPEAKER_00"),
            DiarizationSegment(2.1, 4.0, "SPEAKER_01"),
            DiarizationSegment(4.0, 6.0, "SPEAKER_00"),
        ]

        reference_result = DiarizationResult(
            segments=reference_segments,
            speakers=["SPEAKER_00", "SPEAKER_01"],
            speaker_count=2,
            duration=6.0,
            model_name="test",
            processing_time=1.0,
            device="cpu",
            created_at=None,
        )

        predicted_result = DiarizationResult(
            segments=predicted_segments,
            speakers=["SPEAKER_00", "SPEAKER_01"],
            speaker_count=2,
            duration=6.0,
            model_name="test",
            processing_time=1.0,
            device="cpu",
            created_at=None,
        )

        result = self.processor.evaluate_der(predicted_result, reference_result)

        assert result.success
        assert result.data["data"]["der_score"] == 0.05
        assert result.data["data"]["target_met"] is True

    def test_evaluate_der_failure(self):
        """Test DER evaluation failure."""
        # Create invalid results to trigger exception
        reference_result = DiarizationResult(
            segments=[],
            speakers=[],
            speaker_count=0,
            duration=0.0,
            model_name="test",
            processing_time=0.0,
            device="cpu",
            created_at=None,
        )

        predicted_result = DiarizationResult(
            segments=[],
            speakers=[],
            speaker_count=0,
            duration=0.0,
            model_name="test",
            processing_time=0.0,
            device="cpu",
            created_at=None,
        )

        with patch("pyannote.metrics.diarization.DiarizationErrorRate", side_effect=Exception("DER failed")):
            result = self.processor.evaluate_der(predicted_result, reference_result)

            assert not result.success
            assert "DER evaluation failed" in result.error

    @patch("pyannote.audio.Pipeline.from_pretrained")
    def test_estimate_speaker_count_success(self, mock_pipeline):
        """Test speaker count estimation."""
        mock_model = Mock()
        mock_pipeline.return_value = mock_model

        # Mock diarization result with 3 speakers
        mock_diarization_result = Mock()
        mock_diarization_result.itertracks = Mock(
            return_value=[
                (Mock(), None, "SPEAKER_00"),
                (Mock(), None, "SPEAKER_01"),
                (Mock(), None, "SPEAKER_02"),
            ]
        )
        mock_model.return_value = mock_diarization_result

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
            audio_file.write(b"fake_audio")
            audio_file_path = audio_file.name

        try:
            result = self.processor.estimate_speaker_count(audio_file_path)

            assert result.success
            assert result.data["data"]["estimated_speaker_count"] == 3
            assert result.data["data"]["speakers"] == ["SPEAKER_00", "SPEAKER_01", "SPEAKER_02"]
            assert result.data["data"]["confidence"] == "medium"

        finally:
            Path(audio_file_path).unlink()

    @patch("pyannote.audio.Pipeline.from_pretrained")
    def test_estimate_speaker_count_failure(self, mock_pipeline):
        """Test speaker count estimation failure."""
        mock_model = Mock()
        mock_pipeline.return_value = mock_model
        mock_model.side_effect = Exception("Estimation failed")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
            audio_file.write(b"fake_audio")
            audio_file_path = audio_file.name

        try:
            result = self.processor.estimate_speaker_count(audio_file_path)

            assert not result.success
            assert "Speaker count estimation failed" in result.error

        finally:
            Path(audio_file_path).unlink()

    def test_handle_overlaps_success(self):
        """Test overlap handling."""
        # Create diarization result with overlapping segments
        segments = [
            DiarizationSegment(0.0, 3.0, "SPEAKER_00"),  # Overlaps with next
            DiarizationSegment(2.0, 5.0, "SPEAKER_01"),  # Overlaps with previous
            DiarizationSegment(6.0, 8.0, "SPEAKER_00"),  # No overlap
        ]

        diarization_result = DiarizationResult(
            segments=segments,
            speakers=["SPEAKER_00", "SPEAKER_01"],
            speaker_count=2,
            duration=8.0,
            model_name="test",
            processing_time=1.0,
            device="cpu",
            created_at=None,
        )

        result = self.processor.handle_overlaps(diarization_result, overlap_threshold=0.1)

        assert result.success
        assert result.data["data"]["total_overlaps"] == 1
        assert result.data["data"]["total_overlap_duration"] == 1.0  # 3.0 - 2.0 = 1.0
        assert result.data["data"]["overlap_percentage"] == 12.5  # 1.0 / 8.0 * 100

    def test_handle_overlaps_no_overlaps(self):
        """Test overlap handling with no overlaps."""
        # Create diarization result with no overlapping segments
        segments = [
            DiarizationSegment(0.0, 2.0, "SPEAKER_00"),
            DiarizationSegment(2.0, 4.0, "SPEAKER_01"),
            DiarizationSegment(4.0, 6.0, "SPEAKER_00"),
        ]

        diarization_result = DiarizationResult(
            segments=segments,
            speakers=["SPEAKER_00", "SPEAKER_01"],
            speaker_count=2,
            duration=6.0,
            model_name="test",
            processing_time=1.0,
            device="cpu",
            created_at=None,
        )

        result = self.processor.handle_overlaps(diarization_result)

        assert result.success
        assert result.data["data"]["total_overlaps"] == 0
        assert result.data["data"]["total_overlap_duration"] == 0.0
        assert result.data["data"]["overlap_percentage"] == 0.0

    def test_handle_overlaps_failure(self):
        """Test overlap handling failure."""
        # Create invalid result to trigger exception
        diarization_result = DiarizationResult(
            segments=None,  # Invalid segments
            speakers=[],
            speaker_count=0,
            duration=0.0,
            model_name="test",
            processing_time=0.0,
            device="cpu",
            created_at=None,
        )

        result = self.processor.handle_overlaps(diarization_result)

        assert not result.success
        assert "Overlap handling failed" in result.error

    def test_get_model_info(self):
        """Test model information retrieval."""
        info = self.processor.get_model_info()

        assert info["model_name"] == "pyannote/speaker-diarization-3.1"
        assert info["device"] == "cpu"
        assert "has_gpu" in info
        assert "cuda_device_count" in info
        assert "pipeline_loaded" in info

    def test_cleanup(self):
        """Test resource cleanup."""
        # Mock pipeline
        self.processor.pipeline = Mock()

        # Test cleanup
        self.processor.cleanup()

        assert self.processor.pipeline is None

    @patch("torch.cuda.empty_cache")
    def test_cleanup_with_cuda(self, mock_empty_cache):
        """Test resource cleanup with CUDA."""
        # Set device to CUDA
        self.processor.device = "cuda"
        self.processor.pipeline = Mock()

        # Test cleanup
        self.processor.cleanup()

        assert self.processor.pipeline is None
        mock_empty_cache.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
