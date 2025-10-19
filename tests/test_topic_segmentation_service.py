"""Tests for Topic Segmentation Service."""

from __future__ import annotations

import pytest

from analysis.topic.topic_segmentation_service import (
    TopicModel,
    TopicSegment,
    TopicSegmentationService,
    get_topic_segmentation_service,
)


class TestTopicSegmentationService:
    """Test topic segmentation service functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = TopicSegmentationService(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.service.cache_size == 100
        assert len(self.service._segmentation_cache) == 0
        assert len(self.service._topic_models) == 0

    def test_segment_fallback(self) -> None:
        """Test topic segmentation with fallback model."""
        # Test with short text that would fail real topic modeling
        short_text = "This is a short text."

        result = self.service.segment_text(short_text, model="fast", use_cache=False)

        # Should succeed with fallback model
        assert result.success
        assert result.data is not None
        assert "segments" in result.data
        assert "topic_model" in result.data
        assert result.data["model"].startswith("fallback")

    def test_segment_empty_text(self) -> None:
        """Test handling of empty text."""
        result = self.service.segment_text("", model="fast")

        assert not result.success
        assert result.status == "bad_request"
        assert "empty" in result.error.lower()

    def test_segment_too_short_text(self) -> None:
        """Test handling of too-short text."""
        result = self.service.segment_text("Short text", model="fast")

        assert not result.success
        assert result.status == "bad_request"
        assert "too short" in result.error.lower()

    def test_segmentation_cache_hit(self) -> None:
        """Test topic segmentation cache functionality."""
        text = "This is a longer text for topic segmentation testing with multiple sentences."

        # First segmentation - cache miss
        result1 = self.service.segment_text(text, model="fast", use_cache=True)
        assert result1.success
        assert result1.data["cache_hit"] is False

        # Second segmentation - should be cache hit
        result2 = self.service.segment_text(text, model="fast", use_cache=True)
        assert result2.success
        assert result2.data["cache_hit"] is True

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some cached segmentations
        self.service.segment_text("Text 1", use_cache=True)
        self.service.segment_text("Text 2", use_cache=True)

        assert len(self.service._segmentation_cache) > 0

        # Clear cache
        result = self.service.clear_cache()

        assert result.success
        assert result.data["cleared_entries"] > 0
        assert len(self.service._segmentation_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        # Add some cached segmentations
        self.service.segment_text("Text 1", model="fast", use_cache=True)
        self.service.segment_text("Text 2", model="balanced", use_cache=True)

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
        assert self.service._select_model("fast") == "fast_topic_model"
        assert self.service._select_model("balanced") == "balanced_topic_model"
        assert self.service._select_model("quality") == "quality_topic_model"
        assert self.service._select_model("unknown") == "balanced_topic_model"  # Default

    def test_text_chunking(self) -> None:
        """Test text chunking functionality."""
        long_text = "Word " * 600  # 600 words

        chunks = self.service._split_text_into_chunks(long_text, max_chunk_size=100)

        assert len(chunks) > 1
        assert all(len(chunk) <= 100 for chunk in chunks)

    def test_transcript_segmentation(self) -> None:
        """Test segmentation of transcript segments."""
        transcript_segments = [
            {"start": 0.0, "end": 5.0, "text": "Hello world"},
            {"start": 5.0, "end": 10.0, "text": "This is a test"},
            {"start": 10.0, "end": 15.0, "text": "Topic modeling"},
        ]

        result = self.service.segment_transcript(transcript_segments, model="fast", use_cache=False)

        assert result.success
        assert result.data is not None
        assert "segments" in result.data
        assert len(result.data["segments"]) >= 1

    def test_transcript_segmentation_empty_list(self) -> None:
        """Test transcript segmentation with empty list."""
        result = self.service.segment_transcript([], model="fast")

        # Should handle gracefully, possibly with fallback
        assert result.success or result.status == "bad_request"


class TestTopicSegmentationServiceSingleton:
    """Test singleton instance management."""

    def test_get_topic_segmentation_service(self) -> None:
        """Test getting singleton instance."""
        service1 = get_topic_segmentation_service()
        service2 = get_topic_segmentation_service()

        # Should return same instance
        assert service1 is service2
        assert isinstance(service1, TopicSegmentationService)


class TestTopicModel:
    """Test topic model data structure."""

    def test_create_topic_model(self) -> None:
        """Test creating topic model."""
        model = TopicModel(
            model_id="test_model",
            num_topics=10,
            coherence_score=0.85,
            topics=["Topic 1", "Topic 2"],
            topic_embeddings=[[0.1, 0.2], [0.3, 0.4]],
            model_type="bertopic",
            created_at="2025-01-17",
            training_data_size=100,
        )

        assert model.model_id == "test_model"
        assert model.num_topics == 10
        assert model.coherence_score == 0.85
        assert len(model.topics) == 2
        assert model.model_type == "bertopic"

    def test_topic_model_to_dict(self) -> None:
        """Test converting topic model to dictionary."""
        model = TopicModel(
            model_id="test",
            num_topics=5,
            coherence_score=0.9,
            topics=["AI", "Technology"],
            topic_embeddings=[],
            model_type="test",
            created_at="2025-01-17",
            training_data_size=50,
        )

        model_dict = model.__dict__

        assert model_dict["model_id"] == "test"
        assert model_dict["num_topics"] == 5
        assert model_dict["coherence_score"] == 0.9


class TestTopicSegment:
    """Test topic segment data structure."""

    def test_create_topic_segment(self) -> None:
        """Test creating topic segment."""
        segment = TopicSegment(
            start_time=0.0,
            end_time=30.0,
            text="This is about artificial intelligence",
            topics=["topic_1", "topic_2"],
            topic_names=["AI", "Technology"],
            coherence_score=0.85,
            dominant_topic="topic_1",
        )

        assert segment.start_time == 0.0
        assert segment.end_time == 30.0
        assert segment.text == "This is about artificial intelligence"
        assert len(segment.topics) == 2
        assert len(segment.topic_names) == 2
        assert segment.coherence_score == 0.85
        assert segment.dominant_topic == "topic_1"

    def test_topic_segment_to_dict(self) -> None:
        """Test converting topic segment to dictionary."""
        segment = TopicSegment(
            start_time=10.0,
            end_time=40.0,
            text="Machine learning discussion",
            topics=["ml"],
            topic_names=["Machine Learning"],
            coherence_score=0.9,
        )

        segment_dict = segment.__dict__

        assert segment_dict["start_time"] == 10.0
        assert segment_dict["end_time"] == 40.0
        assert segment_dict["text"] == "Machine learning discussion"
        assert segment_dict["topics"] == ["ml"]
        assert segment_dict["topic_names"] == ["Machine Learning"]


class TestTopicSegmentationWithMocking:
    """Test topic segmentation service with mocked dependencies."""

    def test_segment_text_with_bertopic_mock(self) -> None:
        """Test text segmentation with BERTopic mocking."""
        # Mock BERTopic model
        mock_model = pytest.importorskip("unittest.mock").MagicMock()
        mock_model.fit_transform.return_value = ([0, 1, 0], [[0.8, 0.2], [0.3, 0.7], [0.9, 0.1]])
        mock_model.get_topic_info.return_value = pytest.importorskip("pandas").DataFrame(
            {"Topic": [0, 1, -1], "Name": ["AI_Topic", "Tech_Topic", "Outliers"]}
        )

        with pytest.importorskip("unittest.mock").patch(
            "analysis.topic.topic_segmentation_service.BERTOPIC_AVAILABLE", True
        ):
            with pytest.importorskip("unittest.mock").patch(
                "analysis.topic.topic_segmentation_service.BERTopic"
            ) as mock_bertopic_class:
                mock_bertopic_class.return_value = mock_model

                service = TopicSegmentationService()

                # Test with longer text
                long_text = "This is about AI. " * 50  # 250+ characters

                result = service.segment_text(long_text, model="balanced", use_cache=False)

                assert result.success
                assert result.data["segments"]
                assert result.data["topic_model"] is not None
                assert result.data["overall_coherence"] > 0

    def test_segment_transcript_with_timing(self) -> None:
        """Test transcript segmentation with timing alignment."""
        transcript_segments = [
            {"start": 0.0, "end": 5.0, "text": "Hello world"},
            {"start": 5.0, "end": 10.0, "text": "AI discussion"},
            {"start": 10.0, "end": 15.0, "text": "Technology talk"},
        ]

        service = TopicSegmentationService()

        # Mock the internal segmentation method
        with pytest.importorskip("unittest.mock").patch.object(service, "_segment_text") as mock_segment:
            mock_segment.return_value = type(
                "SegmentationResult",
                (),
                {
                    "segments": [
                        TopicSegment(
                            start_time=0.0,
                            end_time=30.0,
                            text="[T0@0.0-5.0] Hello world [T1@5.0-10.0] AI discussion [T2@10.0-15.0] Technology talk",
                            topics=["topic_1"],
                            topic_names=["General"],
                            coherence_score=0.8,
                            dominant_topic="topic_1",
                        )
                    ],
                    "topic_model": TopicModel(
                        model_id="test",
                        num_topics=1,
                        coherence_score=0.8,
                        topics=["General"],
                        topic_embeddings=[],
                        model_type="test",
                        created_at="2025-01-17",
                        training_data_size=1,
                    ),
                    "overall_coherence": 0.8,
                    "topic_distribution": {"topic_1": 1.0},
                    "model": "test_model",
                },
            )()

            result = service.segment_transcript(transcript_segments, model="fast", use_cache=False)

            assert result.success
            assert result.data["segments"]
            # Should have aligned segments with correct timing
            assert len(result.data["segments"]) >= 1
