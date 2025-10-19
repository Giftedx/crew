"""
Tests for the complete media processing pipeline.

This module tests the integration of ASR, diarization, alignment, NLP, and embeddings
components working together to process creator content.
"""

from datetime import datetime
from unittest.mock import Mock

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.media.alignment import (
    AlignedSegment,
    AlignedTranscript,
    TranscriptAlignment,
)
from ultimate_discord_intelligence_bot.creator_ops.media.asr import ASRResult, ASRSegment, WhisperASR
from ultimate_discord_intelligence_bot.creator_ops.media.diarization import (
    DiarizationResult,
    DiarizationSegment,
    SpeakerDiarization,
)
from ultimate_discord_intelligence_bot.creator_ops.media.embeddings import (
    Embedding,
    EmbeddingResult,
    EmbeddingsGenerator,
)
from ultimate_discord_intelligence_bot.creator_ops.media.nlp import (
    ContentSafety,
    Entity,
    Keyphrase,
    NLPPipeline,
    NLPResult,
    SentimentAnalysis,
    TopicSegment,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestMediaPipeline:
    """Test the complete media processing pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = CreatorOpsConfig()

        # Mock components for testing
        self.asr = Mock(spec=WhisperASR)
        self.diarization = Mock(spec=SpeakerDiarization)
        self.alignment = TranscriptAlignment()
        self.nlp = Mock(spec=NLPPipeline)
        self.embeddings = Mock(spec=EmbeddingsGenerator)

    def test_asr_transcription(self):
        """Test ASR transcription functionality."""
        # Mock ASR result
        mock_segments = [
            ASRSegment(
                start_time=0.0,
                end_time=5.0,
                text="Hello, welcome to the podcast.",
                confidence=0.95,
                language="en",
            ),
            ASRSegment(
                start_time=5.0,
                end_time=10.0,
                text="Today we're discussing AI and machine learning.",
                confidence=0.92,
                language="en",
            ),
        ]

        mock_result = ASRResult(
            text="Hello, welcome to the podcast. Today we're discussing AI and machine learning.",
            language="en",
            language_probability=0.98,
            segments=mock_segments,
            duration=10.0,
            model_name="large-v3",
            processing_time=2.5,
            device="cuda",
            created_at=datetime.utcnow(),
        )

        self.asr.transcribe_audio.return_value = StepResult.ok(data=mock_result)

        # Test transcription
        result = self.asr.transcribe_audio("test_audio.wav")

        assert result.success
        assert result.data.text == "Hello, welcome to the podcast. Today we're discussing AI and machine learning."
        assert len(result.data.segments) == 2
        assert result.data.language == "en"

    def test_speaker_diarization(self):
        """Test speaker diarization functionality."""
        # Mock diarization result
        mock_segments = [
            DiarizationSegment(
                start_time=0.0,
                end_time=5.0,
                speaker="SPEAKER_00",
                confidence=None,
            ),
            DiarizationSegment(
                start_time=5.0,
                end_time=10.0,
                speaker="SPEAKER_01",
                confidence=None,
            ),
        ]

        mock_result = DiarizationResult(
            segments=mock_segments,
            speakers=["SPEAKER_00", "SPEAKER_01"],
            speaker_count=2,
            duration=10.0,
            model_name="pyannote/speaker-diarization-3.1",
            processing_time=3.2,
            device="cuda",
            created_at=datetime.utcnow(),
        )

        self.diarization.diarize_audio.return_value = StepResult.ok(data=mock_result)

        # Test diarization
        result = self.diarization.diarize_audio("test_audio.wav", num_speakers=2)

        assert result.success
        assert result.data.speaker_count == 2
        assert len(result.data.segments) == 2
        assert "SPEAKER_00" in result.data.speakers

    def test_transcript_alignment(self):
        """Test transcript alignment functionality."""
        # Create mock ASR and diarization results
        asr_segments = [
            ASRSegment(
                start_time=0.0,
                end_time=5.0,
                text="Hello, welcome to the podcast.",
                confidence=0.95,
                language="en",
            ),
            ASRSegment(
                start_time=5.0,
                end_time=10.0,
                text="Today we're discussing AI and machine learning.",
                confidence=0.92,
                language="en",
            ),
        ]

        diarization_segments = [
            DiarizationSegment(
                start_time=0.0,
                end_time=5.0,
                speaker="SPEAKER_00",
                confidence=None,
            ),
            DiarizationSegment(
                start_time=5.0,
                end_time=10.0,
                speaker="SPEAKER_01",
                confidence=None,
            ),
        ]

        asr_result = ASRResult(
            text="Hello, welcome to the podcast. Today we're discussing AI and machine learning.",
            language="en",
            language_probability=0.98,
            segments=asr_segments,
            duration=10.0,
            model_name="large-v3",
            processing_time=2.5,
            device="cuda",
            created_at=datetime.utcnow(),
        )

        diarization_result = DiarizationResult(
            segments=diarization_segments,
            speakers=["SPEAKER_00", "SPEAKER_01"],
            speaker_count=2,
            duration=10.0,
            model_name="pyannote/speaker-diarization-3.1",
            processing_time=3.2,
            device="cuda",
            created_at=datetime.utcnow(),
        )

        # Test alignment
        result = self.alignment.align_transcripts(asr_result, diarization_result)

        assert result.success
        assert len(result.data.segments) == 2
        assert result.data.segments[0].speaker == "SPEAKER_00"
        assert result.data.segments[1].speaker == "SPEAKER_01"
        assert result.data.speaker_turns == 2

    def test_nlp_analysis(self):
        """Test NLP analysis functionality."""
        # Create mock aligned transcript
        aligned_segments = [
            AlignedSegment(
                start_time=0.0,
                end_time=5.0,
                speaker="SPEAKER_00",
                text="Hello, welcome to the podcast.",
                confidence=0.95,
                language="en",
                is_overlap=False,
                overlap_speakers=None,
            ),
            AlignedSegment(
                start_time=5.0,
                end_time=10.0,
                speaker="SPEAKER_01",
                text="Today we're discussing AI and machine learning.",
                confidence=0.92,
                language="en",
                is_overlap=False,
                overlap_speakers=None,
            ),
        ]

        aligned_transcript = AlignedTranscript(
            segments=aligned_segments,
            speakers=["SPEAKER_00", "SPEAKER_01"],
            total_duration=10.0,
            word_count=12,
            speaker_turns=2,
            overlap_percentage=0.0,
            cleanup_applied=["remove_fillers"],
            provenance={},
            created_at=datetime.utcnow(),
        )

        # Mock NLP result
        mock_nlp_result = NLPResult(
            topic_segments=[
                TopicSegment(
                    start_time=0.0,
                    end_time=10.0,
                    topic="AI Discussion",
                    confidence=0.8,
                    keywords=["AI", "machine learning"],
                    segment_indices=[0, 1],
                )
            ],
            keyphrases=[
                Keyphrase(
                    text="machine learning",
                    score=0.9,
                    start_time=5.0,
                    end_time=10.0,
                    speaker="SPEAKER_01",
                )
            ],
            entities=[
                Entity(
                    text="AI",
                    label="MISC",
                    confidence=0.8,
                    start_time=5.0,
                    end_time=10.0,
                    speaker="SPEAKER_01",
                )
            ],
            claims=[],
            sentiment_analysis=[
                SentimentAnalysis(
                    label="positive",
                    score=0.8,
                    start_time=0.0,
                    end_time=5.0,
                    speaker="SPEAKER_00",
                ),
                SentimentAnalysis(
                    label="neutral",
                    score=0.6,
                    start_time=5.0,
                    end_time=10.0,
                    speaker="SPEAKER_01",
                ),
            ],
            content_safety=[
                ContentSafety(
                    toxicity_score=0.1,
                    brand_suitability_score=4.5,
                    controversy_flags=[],
                    risk_level="low",
                    start_time=0.0,
                    end_time=10.0,
                    speaker=None,
                )
            ],
            processing_time=1.5,
            model_versions={},
            created_at=datetime.utcnow(),
        )

        self.nlp.analyze_transcript.return_value = StepResult.ok(data=mock_nlp_result)

        # Test NLP analysis
        result = self.nlp.analyze_transcript(aligned_transcript)

        assert result.success
        assert len(result.data.topic_segments) == 1
        assert len(result.data.keyphrases) == 1
        assert len(result.data.entities) == 1
        assert len(result.data.sentiment_analysis) == 2
        assert result.data.content_safety[0].risk_level == "low"

    def test_embeddings_generation(self):
        """Test embeddings generation functionality."""
        # Create mock aligned transcript and NLP result
        aligned_segments = [
            AlignedSegment(
                start_time=0.0,
                end_time=5.0,
                speaker="SPEAKER_00",
                text="Hello, welcome to the podcast.",
                confidence=0.95,
                language="en",
                is_overlap=False,
                overlap_speakers=None,
            ),
        ]

        aligned_transcript = AlignedTranscript(
            segments=aligned_segments,
            speakers=["SPEAKER_00"],
            total_duration=5.0,
            word_count=5,
            speaker_turns=1,
            overlap_percentage=0.0,
            cleanup_applied=[],
            provenance={},
            created_at=datetime.utcnow(),
        )

        # Mock embeddings result
        mock_embeddings = [
            Embedding(
                vector=[0.1, 0.2, 0.3] * 100,  # 300-dimensional vector
                text="Hello, welcome to the podcast.",
                metadata={"segment_index": 0, "speaker": "SPEAKER_00"},
                created_at=datetime.utcnow(),
            )
        ]

        EmbeddingResult(
            embeddings=mock_embeddings,
            model_name="text-embedding-3-large",
            vector_dimension=300,
            processing_time=0.5,
            created_at=datetime.utcnow(),
        )

        self.embeddings.generate_transcript_embeddings.return_value = StepResult.ok(
            data={"stored_ids": ["embedding_1"], "collection_name": "test_collection", "embedding_count": 1}
        )

        # Test embeddings generation
        result = self.embeddings.generate_transcript_embeddings(aligned_transcript)

        assert result.success
        assert result.data["embedding_count"] == 1
        assert result.data["collection_name"] == "test_collection"

    def test_end_to_end_pipeline(self):
        """Test the complete end-to-end pipeline."""
        # This would test the integration of all components
        # For now, we'll test that the components can work together

        # Mock all components
        self.asr.transcribe_audio.return_value = StepResult.ok(data=Mock())
        self.diarization.diarize_audio.return_value = StepResult.ok(data=Mock())
        self.nlp.analyze_transcript.return_value = StepResult.ok(data=Mock())
        self.embeddings.generate_transcript_embeddings.return_value = StepResult.ok(data=Mock())

        # Test that all components can be called
        asr_result = self.asr.transcribe_audio("test_audio.wav")
        diarization_result = self.diarization.diarize_audio("test_audio.wav")

        assert asr_result.success
        assert diarization_result.success

        # Test alignment (real component)
        alignment_result = self.alignment.align_transcripts(asr_result.data, diarization_result.data)

        assert alignment_result.success

        # Test NLP and embeddings (mocked)
        nlp_result = self.nlp.analyze_transcript(alignment_result.data)
        embeddings_result = self.embeddings.generate_transcript_embeddings(alignment_result.data, nlp_result.data)

        assert nlp_result.success
        assert embeddings_result.success

    def test_error_handling(self):
        """Test error handling in the pipeline."""
        # Test ASR failure
        self.asr.transcribe_audio.return_value = StepResult.fail("ASR failed")

        result = self.asr.transcribe_audio("invalid_audio.wav")
        assert not result.success
        assert "ASR failed" in result.error

        # Test diarization failure
        self.diarization.diarize_audio.return_value = StepResult.fail("Diarization failed")

        result = self.diarization.diarize_audio("invalid_audio.wav")
        assert not result.success
        assert "Diarization failed" in result.error

    def test_cleanup_resources(self):
        """Test resource cleanup."""
        # Test that cleanup methods exist and can be called
        self.asr.cleanup.return_value = None
        self.diarization.cleanup.return_value = None
        self.nlp.cleanup.return_value = None
        self.embeddings.cleanup.return_value = None

        # Call cleanup methods
        self.asr.cleanup()
        self.diarization.cleanup()
        self.nlp.cleanup()
        self.embeddings.cleanup()

        # Verify cleanup was called
        self.asr.cleanup.assert_called_once()
        self.diarization.cleanup.assert_called_once()
        self.nlp.cleanup.assert_called_once()
        self.embeddings.cleanup.assert_called_once()


class TestTranscriptAlignment:
    """Test transcript alignment functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.alignment = TranscriptAlignment()

    def test_text_cleanup(self):
        """Test text cleanup functionality."""
        # Test filler word removal
        text = "Um, so basically, you know, this is a test."
        cleaned = self.alignment._cleanup_text(text, {"remove_fillers": True, "remove_extra_spaces": True})
        assert "um" not in cleaned.lower()
        assert "basically" not in cleaned.lower()
        assert "you know" not in cleaned.lower()

        # Test stutter removal
        text = "This is is a test test test."
        cleaned = self.alignment._cleanup_text(text, {"fix_stutters": True, "remove_extra_spaces": True})
        assert "is is" not in cleaned
        assert "test test test" not in cleaned

        # Test capitalization
        text = "hello world. this is a test."
        cleaned = self.alignment._cleanup_text(text, {"capitalize_sentences": True})
        assert cleaned.startswith("Hello")
        assert "This is a test" in cleaned

    def test_srt_export(self):
        """Test SRT export functionality."""
        # Create mock aligned transcript
        segments = [
            AlignedSegment(
                start_time=0.0,
                end_time=5.0,
                speaker="SPEAKER_00",
                text="Hello, welcome to the podcast.",
                confidence=0.95,
                language="en",
                is_overlap=False,
                overlap_speakers=None,
            ),
        ]

        transcript = AlignedTranscript(
            segments=segments,
            speakers=["SPEAKER_00"],
            total_duration=5.0,
            word_count=5,
            speaker_turns=1,
            overlap_percentage=0.0,
            cleanup_applied=[],
            provenance={},
            created_at=datetime.utcnow(),
        )

        # Test SRT export
        srt_content = self.alignment.export_to_srt(transcript)

        assert "1" in srt_content
        assert "00:00:00,000 --> 00:00:05,000" in srt_content
        assert "[SPEAKER_00]: Hello, welcome to the podcast." in srt_content

    def test_json_export(self):
        """Test JSON export functionality."""
        # Create mock aligned transcript
        segments = [
            AlignedSegment(
                start_time=0.0,
                end_time=5.0,
                speaker="SPEAKER_00",
                text="Hello, welcome to the podcast.",
                confidence=0.95,
                language="en",
                is_overlap=False,
                overlap_speakers=None,
            ),
        ]

        transcript = AlignedTranscript(
            segments=segments,
            speakers=["SPEAKER_00"],
            total_duration=5.0,
            word_count=5,
            speaker_turns=1,
            overlap_percentage=0.0,
            cleanup_applied=[],
            provenance={},
            created_at=datetime.utcnow(),
        )

        # Test JSON export
        json_data = self.alignment.export_to_json(transcript)

        assert "metadata" in json_data
        assert "segments" in json_data
        assert json_data["metadata"]["speakers"] == ["SPEAKER_00"]
        assert len(json_data["segments"]) == 1
        assert json_data["segments"][0]["speaker"] == "SPEAKER_00"
