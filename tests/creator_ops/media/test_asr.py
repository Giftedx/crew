"""
Unit tests for Automatic Speech Recognition (ASR) functionality.

Tests cover:
- Whisper model initialization and configuration
- Audio file processing and transcription
- Language detection and confidence scoring
- Batch processing capabilities
- Error handling and edge cases
- Performance metrics (WER <10% target)
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.media import (
    WhisperASR,
)
from ultimate_discord_intelligence_bot.creator_ops.media.asr import (
    ASRResult,
)


class TestWhisperASR:
    """Test suite for ASR processor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = CreatorOpsConfig()
        # Mock _initialize_models to avoid ML dependency errors
        with patch.object(WhisperASR, "_initialize_models", return_value=None):
            self.processor = WhisperASR(model_name="base", device="cpu", config=self.config)
            self.processor.model = None
            self.processor.faster_model = None

    def test_initialization(self):
        """Test ASR processor initialization."""
        assert self.processor.model_name == "base"
        assert self.processor.device == "cpu"
        assert self.processor.config is not None
        # Model may be None if ML deps not available

    @patch("faster_whisper.WhisperModel")
    def test_transcribe_audio_success(self, mock_whisper_model):
        """Test successful audio transcription."""
        # Mock model and transcription result
        mock_model = Mock()
        mock_whisper_model.return_value = mock_model

        mock_segments = [
            {
                "start": 0.0,
                "end": 2.5,
                "text": "Hello world",
                "words": [
                    {"start": 0.0, "end": 1.0, "word": "Hello"},
                    {"start": 1.0, "end": 2.5, "word": "world"},
                ],
            },
            {
                "start": 2.5,
                "end": 5.0,
                "text": "This is a test",
                "words": [
                    {"start": 2.5, "end": 3.5, "word": "This"},
                    {"start": 3.5, "end": 5.0, "word": "is a test"},
                ],
            },
        ]

        mock_transcribe_result = (
            mock_segments,
            {
                "language": "en",
                "language_probability": 0.95,
                "duration": 5.0,
                "all_language_probs": {"en": 0.95, "es": 0.03, "fr": 0.02},
            },
        )

        mock_model.transcribe.return_value = mock_transcribe_result

        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
            audio_file.write(b"fake_audio_data")
            audio_file_path = audio_file.name

        try:
            result = self.processor.transcribe_audio(audio_file_path)

            assert result.success
            assert "result" in result.data
            asr_result = result.data["result"]
            assert isinstance(asr_result, ASRResult)
            assert asr_result.text == "Hello world This is a test"
            assert asr_result.language == "en"
            assert asr_result.language_probability == 0.95
            assert len(asr_result.segments) == 2
            assert asr_result.segments[0].text == "Hello world"
            assert asr_result.segments[0].start_time == 0.0
            assert asr_result.segments[0].end_time == 2.5

        finally:
            Path(audio_file_path).unlink()

    @patch("faster_whisper.WhisperModel")
    def test_transcribe_audio_file_not_found(self, mock_whisper_model):
        """Test transcription with non-existent audio file."""
        result = self.processor.transcribe_audio("nonexistent_file.wav")

        assert not result.success
        assert "Audio file not found" in result.error

    @patch("faster_whisper.WhisperModel")
    def test_transcribe_audio_transcription_error(self, mock_whisper_model):
        """Test transcription with model error."""
        mock_model = Mock()
        mock_whisper_model.return_value = mock_model
        mock_model.transcribe.side_effect = Exception("Transcription failed")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
            audio_file.write(b"fake_audio_data")
            audio_file_path = audio_file.name

        try:
            result = self.processor.transcribe_audio(audio_file_path)

            assert not result.success
            assert "Transcription failed" in result.error

        finally:
            Path(audio_file_path).unlink()

    def test_calculate_wer_success(self):
        """Test Word Error Rate calculation."""
        reference = "Hello world this is a test"
        hypothesis = "Hello world this is test"

        wer = self.processor._calculate_wer(reference, hypothesis)

        # Should be 1/6 = 0.167 (1 word error out of 6 words)
        assert abs(wer - 0.167) < 0.01

    def test_calculate_wer_perfect_match(self):
        """Test WER calculation with perfect match."""
        reference = "Hello world"
        hypothesis = "Hello world"

        wer = self.processor._calculate_wer(reference, hypothesis)

        assert wer == 0.0

    def test_calculate_wer_completely_wrong(self):
        """Test WER calculation with completely wrong transcription."""
        reference = "Hello world"
        hypothesis = "Goodbye universe"

        wer = self.processor._calculate_wer(reference, hypothesis)

        assert wer == 1.0

    def test_calculate_wer_empty_reference(self):
        """Test WER calculation with empty reference."""
        reference = ""
        hypothesis = "Hello world"

        wer = self.processor._calculate_wer(reference, hypothesis)

        assert wer == 1.0

    def test_calculate_wer_empty_hypothesis(self):
        """Test WER calculation with empty hypothesis."""
        reference = "Hello world"
        hypothesis = ""

        wer = self.processor._calculate_wer(reference, hypothesis)

        assert wer == 1.0

    @patch("faster_whisper.WhisperModel")
    def test_batch_transcribe_success(self, mock_whisper_model):
        """Test batch transcription of multiple audio files."""
        mock_model = Mock()
        mock_whisper_model.return_value = mock_model

        mock_transcribe_result = (
            [{"start": 0.0, "end": 2.0, "text": "Test transcription", "words": []}],
            {"language": "en", "language_probability": 0.9, "duration": 2.0},
        )
        mock_model.transcribe.return_value = mock_transcribe_result

        # Create temporary audio files
        audio_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
                audio_file.write(f"fake_audio_data_{i}".encode())
                audio_files.append(audio_file.name)

        try:
            results = self.processor.batch_transcribe(audio_files)

            assert len(results) == 3
            for result in results:
                assert result.success
                assert "result" in result.data
                asr_result = result.data["result"]
                assert asr_result.text == "Test transcription"

        finally:
            for audio_file in audio_files:
                Path(audio_file).unlink()

    @patch("faster_whisper.WhisperModel")
    def test_batch_transcribe_partial_failure(self, mock_whisper_model):
        """Test batch transcription with some failures."""
        mock_model = Mock()
        mock_whisper_model.return_value = mock_model

        # First call succeeds, second fails
        mock_transcribe_result = (
            [{"start": 0.0, "end": 2.0, "text": "Test transcription", "words": []}],
            {"language": "en", "language_probability": 0.9, "duration": 2.0},
        )

        def side_effect(*args, **kwargs):
            if mock_model.transcribe.call_count == 1:
                return mock_transcribe_result
            else:
                raise Exception("Transcription failed")

        mock_model.transcribe.side_effect = side_effect

        # Create temporary audio files
        audio_files = []
        for i in range(2):
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
                audio_file.write(f"fake_audio_data_{i}".encode())
                audio_files.append(audio_file.name)

        try:
            results = self.processor.batch_transcribe(audio_files)

            assert len(results) == 2
            assert results[0].success
            assert not results[1].success

        finally:
            for audio_file in audio_files:
                Path(audio_file).unlink()

    def test_language_detection(self):
        """Test automatic language detection."""
        # Test with language=None to trigger detection
        config = WhisperConfig(
            model_name="base",
            device="cpu",
            language=None,  # Auto-detect
        )
        processor = WhisperASR(config=config)

        @patch("faster_whisper.WhisperModel")
        def test_detection(mock_whisper_model):
            mock_model = Mock()
            mock_whisper_model.return_value = mock_model

            mock_transcribe_result = (
                [{"start": 0.0, "end": 2.0, "text": "Hola mundo", "words": []}],
                {"language": "es", "language_probability": 0.95, "duration": 2.0},
            )
            mock_model.transcribe.return_value = mock_transcribe_result

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
                audio_file.write(b"fake_spanish_audio")
                audio_file_path = audio_file.name

            try:
                result = processor.transcribe_audio(audio_file_path)

                assert result.success
                asr_result = result.data["result"]
                assert asr_result.language == "es"
                assert asr_result.language_probability == 0.95

            finally:
                Path(audio_file_path).unlink()

        test_detection()

    def test_confidence_threshold_filtering(self):
        """Test filtering based on confidence thresholds."""
        config = WhisperConfig(
            model_name="base",
            device="cpu",
            no_speech_threshold=0.5,
            log_prob_threshold=-0.5,
        )
        processor = WhisperASR(config=config)

        @patch("faster_whisper.WhisperModel")
        def test_filtering(mock_whisper_model):
            mock_model = Mock()
            mock_whisper_model.return_value = mock_model

            # Mock segments with varying confidence
            mock_segments = [
                {
                    "start": 0.0,
                    "end": 2.0,
                    "text": "High confidence",
                    "words": [],
                    "no_speech_prob": 0.1,  # Low no_speech_prob = high confidence
                },
                {
                    "start": 2.0,
                    "end": 4.0,
                    "text": "Low confidence",
                    "words": [],
                    "no_speech_prob": 0.8,  # High no_speech_prob = low confidence
                },
            ]

            mock_transcribe_result = (
                mock_segments,
                {"language": "en", "language_probability": 0.9, "duration": 4.0},
            )
            mock_model.transcribe.return_value = mock_transcribe_result

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
                audio_file.write(b"fake_audio")
                audio_file_path = audio_file.name

            try:
                result = processor.transcribe_audio(audio_file_path)

                assert result.success
                asr_result = result.data["result"]
                # Should filter out low confidence segments
                assert len(asr_result.segments) == 1
                assert asr_result.segments[0].text == "High confidence"

            finally:
                Path(audio_file_path).unlink()

        test_filtering()

    def test_performance_metrics(self):
        """Test performance metrics calculation."""
        # Mock timing
        with patch("time.time", side_effect=[0.0, 2.5]):
            result = self.processor._calculate_performance_metrics(5.0, "base")

        assert result["processing_time"] == 2.5
        assert result["real_time_factor"] == 0.5  # 2.5s to process 5s audio
        assert result["model_name"] == "base"

    def test_memory_cleanup(self):
        """Test proper memory cleanup after processing."""
        # This test ensures that temporary files and model resources are properly cleaned up
        with patch("faster_whisper.WhisperModel") as mock_whisper_model:
            mock_model = Mock()
            mock_whisper_model.return_value = mock_model

            mock_transcribe_result = (
                [{"start": 0.0, "end": 2.0, "text": "Test", "words": []}],
                {"language": "en", "language_probability": 0.9, "duration": 2.0},
            )
            mock_model.transcribe.return_value = mock_transcribe_result

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
                audio_file.write(b"fake_audio")
                audio_file_path = audio_file.name

            try:
                result = self.processor.transcribe_audio(audio_file_path)

                assert result.success
                # Verify temporary file was cleaned up
                assert not Path(audio_file_path).exists()

            finally:
                # Clean up in case test fails
                if Path(audio_file_path).exists():
                    Path(audio_file_path).unlink()

    def test_concurrent_transcription(self):
        """Test concurrent transcription requests."""
        import threading

        results = []
        errors = []

        def transcribe_worker(audio_file_path):
            try:
                with patch("faster_whisper.WhisperModel") as mock_whisper_model:
                    mock_model = Mock()
                    mock_whisper_model.return_value = mock_model

                    mock_transcribe_result = (
                        [
                            {
                                "start": 0.0,
                                "end": 2.0,
                                "text": f"Test {audio_file_path}",
                                "words": [],
                            }
                        ],
                        {
                            "language": "en",
                            "language_probability": 0.9,
                            "duration": 2.0,
                        },
                    )
                    mock_model.transcribe.return_value = mock_transcribe_result

                    result = self.processor.transcribe_audio(audio_file_path)
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # Create temporary audio files
        audio_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
                audio_file.write(f"fake_audio_{i}".encode())
                audio_files.append(audio_file.name)

        try:
            # Start multiple threads
            threads = []
            for audio_file in audio_files:
                thread = threading.Thread(target=transcribe_worker, args=(audio_file,))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Verify all requests succeeded
            assert len(results) == 3
            assert len(errors) == 0
            assert all(result.success for result in results)

        finally:
            for audio_file in audio_files:
                if Path(audio_file).exists():
                    Path(audio_file).unlink()


if __name__ == "__main__":
    pytest.main([__file__])
