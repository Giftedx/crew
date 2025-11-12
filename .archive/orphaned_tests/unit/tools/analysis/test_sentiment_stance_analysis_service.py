"""Tests for Sentiment and Stance Analysis Service."""

from __future__ import annotations

from analysis.sentiment.sentiment_stance_analysis_service import (
    EmotionAnalysis,
    SentimentAnalysis,
    SentimentStanceAnalysisService,
    StanceAnalysis,
    get_sentiment_stance_analysis_service,
)


class TestSentimentStanceAnalysisService:
    """Test sentiment and stance analysis service functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = SentimentStanceAnalysisService(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.service.cache_size == 100
        assert len(self.service._analysis_cache) == 0
        assert self.service._sentiment_pipeline is None
        assert self.service._emotion_pipeline is None
        assert self.service._stance_pipeline is None

    def test_analyze_fallback(self) -> None:
        """Test analysis with fallback rule-based method."""
        text = "This is amazing content! I love it so much."

        result = self.service.analyze_text(text, model="fast", use_cache=False)

        # Should succeed with rule-based analysis
        assert result.success
        assert result.data is not None
        assert "sentiment" in result.data
        assert "emotion" in result.data
        assert "stance" in result.data
        assert "rhetorical" in result.data

    def test_analyze_empty_text(self) -> None:
        """Test handling of empty text."""
        result = self.service.analyze_text("", model="fast")

        assert not result.success
        assert result.status == "bad_request"
        assert "empty" in result.error.lower()

    def test_analyze_short_text(self) -> None:
        """Test handling of very short text."""
        result = self.service.analyze_text("Hi", model="fast")

        assert result.success  # Should work with fallback

    def test_analysis_cache_hit(self) -> None:
        """Test analysis cache functionality."""
        text = "This is a test text for caching purposes."

        # First analysis - cache miss
        result1 = self.service.analyze_text(text, model="fast", use_cache=True)
        assert result1.success
        assert result1.data["cache_hit"] is False

        # Second analysis - should be cache hit
        result2 = self.service.analyze_text(text, model="fast", use_cache=True)
        assert result2.success
        assert result2.data["cache_hit"] is True

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some cached analyses
        self.service.analyze_text("Text 1", use_cache=True)
        self.service.analyze_text("Text 2", use_cache=True)

        assert len(self.service._analysis_cache) > 0

        # Clear cache
        result = self.service.clear_cache()

        assert result.success
        assert result.data["cleared_entries"] > 0
        assert len(self.service._analysis_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        # Add some cached analyses
        self.service.analyze_text("Text 1", model="fast", use_cache=True)
        self.service.analyze_text("Text 2", model="balanced", use_cache=True)

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
        assert self.service._select_model("fast") == "fast_analysis"
        assert self.service._select_model("balanced") == "balanced_analysis"
        assert self.service._select_model("quality") == "quality_analysis"
        assert self.service._select_model("unknown") == "balanced_analysis"  # Default

    def test_analyze_segments(self) -> None:
        """Test analysis of multiple segments."""
        segments = [
            {"text": "This is amazing content!", "speaker": "Host"},
            {"text": "I completely agree.", "speaker": "Guest"},
            {"text": "What do you think about this?", "speaker": "Host"},
        ]

        result = self.service.analyze_segments(segments, model="fast", use_cache=False)

        assert result.success
        assert result.data is not None
        assert "results" in result.data
        assert result.data["total_segments"] == 3
        assert len(result.data["results"]) >= 2  # Some segments might be too short

    def test_sentiment_analysis_rules(self) -> None:
        """Test rule-based sentiment analysis."""
        # Test positive text
        positive_result = self.service._analyze_sentiment_rules("This is amazing and wonderful!")
        assert positive_result.sentiment == "positive"
        assert positive_result.confidence > 0.5

        # Test negative text
        negative_result = self.service._analyze_sentiment_rules("This is terrible and awful!")
        assert negative_result.sentiment == "negative"
        assert negative_result.confidence > 0.5

        # Test neutral text
        neutral_result = self.service._analyze_sentiment_rules("This is a statement.")
        assert neutral_result.sentiment == "neutral"

    def test_emotion_analysis_rules(self) -> None:
        """Test rule-based emotion analysis."""
        # Test joyful text
        joy_result = self.service._analyze_emotion_rules("I'm so happy and excited!")
        assert joy_result.primary_emotion == "joy"
        assert "joy" in joy_result.emotion_scores

        # Test angry text
        anger_result = self.service._analyze_emotion_rules("This makes me so angry!")
        assert anger_result.primary_emotion == "anger"
        assert "anger" in anger_result.emotion_scores

    def test_stance_analysis(self) -> None:
        """Test stance analysis."""
        # Test agreement
        agree_result = self.service._analyze_stance("I completely agree with you.")
        assert agree_result.stance == "agree"
        assert agree_result.stance_type == "explicit"

        # Test disagreement
        disagree_result = self.service._analyze_stance("I disagree with that statement.")
        assert disagree_result.stance == "disagree"
        assert disagree_result.stance_type == "explicit"

        # Test questioning
        question_result = self.service._analyze_stance("What do you think about this?")
        assert question_result.stance == "questioning"
        assert question_result.stance_type == "rhetorical"

    def test_rhetorical_analysis(self) -> None:
        """Test rhetorical device analysis."""
        # Test question
        question_result = self.service._analyze_rhetorical("What is the meaning of life?")
        assert question_result.has_question is True

        # Test exclamation
        exclamation_result = self.service._analyze_rhetorical("This is amazing!")
        assert exclamation_result.has_exclamation is True

        # Test emphasis
        emphasis_result = self.service._analyze_rhetorical("This is VERY important!")
        assert emphasis_result.has_emphasis is True
        assert "VERY" in emphasis_result.emphasis_words


class TestSentimentStanceAnalysisServiceSingleton:
    """Test singleton instance management."""

    def test_get_sentiment_stance_analysis_service(self) -> None:
        """Test getting singleton instance."""
        service1 = get_sentiment_stance_analysis_service()
        service2 = get_sentiment_stance_analysis_service()

        # Should return same instance
        assert service1 is service2
        assert isinstance(service1, SentimentStanceAnalysisService)


class TestSentimentAnalysis:
    """Test sentiment analysis data structure."""

    def test_create_sentiment_analysis(self) -> None:
        """Test creating sentiment analysis."""
        sentiment = SentimentAnalysis(
            sentiment="positive",
            confidence=0.85,
            intensity=0.7,
        )

        assert sentiment.sentiment == "positive"
        assert sentiment.confidence == 0.85
        assert sentiment.intensity == 0.7

    def test_sentiment_analysis_defaults(self) -> None:
        """Test sentiment analysis with default values."""
        sentiment = SentimentAnalysis(
            sentiment="neutral",
            confidence=0.5,
        )

        assert sentiment.sentiment == "neutral"
        assert sentiment.confidence == 0.5
        assert sentiment.intensity == 0.0  # Default intensity


class TestEmotionAnalysis:
    """Test emotion analysis data structure."""

    def test_create_emotion_analysis(self) -> None:
        """Test creating emotion analysis."""
        emotion = EmotionAnalysis(
            primary_emotion="joy",
            confidence=0.9,
            emotion_scores={
                "joy": 0.9,
                "sadness": 0.1,
                "anger": 0.0,
            },
        )

        assert emotion.primary_emotion == "joy"
        assert emotion.confidence == 0.9
        assert "joy" in emotion.emotion_scores
        assert emotion.emotion_scores["joy"] == 0.9

    def test_emotion_analysis_defaults(self) -> None:
        """Test emotion analysis with default values."""
        emotion = EmotionAnalysis(
            primary_emotion="neutral",
            confidence=0.5,
        )

        assert emotion.primary_emotion == "neutral"
        assert emotion.confidence == 0.5
        assert emotion.emotion_scores == {}


class TestStanceAnalysis:
    """Test stance analysis data structure."""

    def test_create_stance_analysis(self) -> None:
        """Test creating stance analysis."""
        stance = StanceAnalysis(
            stance="agree",
            confidence=0.8,
            stance_type="explicit",
        )

        assert stance.stance == "agree"
        assert stance.confidence == 0.8
        assert stance.stance_type == "explicit"

    def test_stance_analysis_defaults(self) -> None:
        """Test stance analysis with default values."""
        stance = StanceAnalysis(
            stance="neutral",
            confidence=0.5,
        )

        assert stance.stance == "neutral"
        assert stance.confidence == 0.5
        assert stance.stance_type == "implicit"  # Default stance type


class TestSentimentStanceAnalysisWithMocking:
    """Test sentiment analysis service with mocked dependencies."""

    def test_analyze_with_speaker_context(self) -> None:
        """Test analysis with speaker context."""
        text = "This is amazing content!"
        speaker = "Host"

        result = self.service.analyze_text(text, speaker=speaker, model="fast", use_cache=False)

        assert result.success

        # Should preserve speaker context
        assert result.data["speaker"] == "Host"
        assert result.data["text_segment"] == text

    def test_analyze_with_timestamp(self) -> None:
        """Test analysis with timestamp context."""
        text = "Great discussion!"
        timestamp = 45.0

        result = self.service.analyze_text(text, timestamp=timestamp, model="fast", use_cache=False)

        assert result.success
        assert result.data["timestamp"] == 45.0

    def test_analyze_segments_with_context(self) -> None:
        """Test analysis of segments with speaker context."""
        segments = [
            {
                "text": "This is amazing!",
                "speaker": "Host",
                "timestamp": 0.0,
            },
            {
                "text": "I completely agree.",
                "speaker": "Guest",
                "timestamp": 30.0,
            },
        ]

        result = self.service.analyze_segments(segments, model="fast", use_cache=False)

        assert result.success
        assert result.data["total_segments"] == 2

        # Check that results preserve context
        results = result.data["results"]
        if results:
            # Should have speaker information
            speakers = [r.get("speaker") for r in results if r.get("speaker")]
            assert len(speakers) >= 1
