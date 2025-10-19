"""Tests for Smart Clip Composer Service."""

from __future__ import annotations

from features.smart_clip_composer.smart_clip_composer_service import (
    ClipSuggestion,
    ClipVariant,
    SmartClipComposerService,
    get_smart_clip_composer_service,
)


class TestSmartClipComposerService:
    """Test smart clip composer service functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.composer = SmartClipComposerService(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.composer.cache_size == 100
        assert len(self.composer._composition_cache) == 0
        assert len(self.composer._signal_weights) == 5

    def test_generate_clip_suggestions_basic(self) -> None:
        """Test basic clip suggestion generation."""
        content_analysis = {
            "duration": 3600.0,
            "segments": [
                {"start_time": 0.0, "end_time": 30.0, "text": "This is a test segment."},
            ],
            "highlights": [
                {"start_time": 0.0, "end_time": 30.0, "highlight_score": 0.8},
            ],
        }

        result = self.composer.generate_clip_suggestions(content_analysis, max_clips=5, use_cache=False)

        assert result.success
        assert result.data is not None
        assert "suggestions" in result.data
        assert result.data["total_content_duration"] == 3600.0

    def test_generate_clip_suggestions_empty_analysis(self) -> None:
        """Test handling of empty content analysis."""
        result = self.composer.generate_clip_suggestions({}, use_cache=False)

        assert not result.success
        assert result.status == "bad_request"
        assert "cannot be empty" in result.error.lower()

    def test_generate_clip_variants(self) -> None:
        """Test A/B testing variant generation."""
        suggestion = ClipSuggestion(
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            title="Test Clip",
            description="Test description",
            thumbnail_text="Test thumbnail",
            confidence_score=0.8,
            signal_scores={"audio_energy": 0.7, "semantic_novelty": 0.6},
            suggested_platforms=["youtube_shorts"],
            estimated_engagement=0.75,
        )

        variants = self.composer.generate_clip_variants(suggestion, num_variants=2)

        assert len(variants) == 2
        assert all(variant.variant_id.startswith("variant_") for variant in variants)
        assert all(variant.expected_performance > 0 for variant in variants)

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some cached compositions
        self.composer.generate_clip_suggestions({"duration": 100}, use_cache=True)

        assert len(self.composer._composition_cache) > 0

        # Clear cache
        result = self.composer.clear_cache()

        assert result.success
        assert result.data["cleared_entries"] > 0
        assert len(self.composer._composition_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        # Add some cached compositions
        self.composer.generate_clip_suggestions({"duration": 100}, use_cache=True)

        result = self.composer.get_cache_stats()

        assert result.success
        assert result.data is not None
        assert "total_cached" in result.data
        assert "cache_size_limit" in result.data

        assert result.data["total_cached"] >= 1
        assert result.data["cache_size_limit"] == 100

    def test_model_selection(self) -> None:
        """Test model selection logic."""
        assert self.composer._select_model("fast") == "fast_composition"
        assert self.composer._select_model("balanced") == "balanced_composition"
        assert self.composer._select_model("quality") == "quality_composition"
        assert self.composer._select_model("unknown") == "balanced_composition"  # Default

    def test_score_suggestions(self) -> None:
        """Test suggestion scoring and ranking."""
        suggestions = [
            ClipSuggestion(0, 30, 30, "Title 1", "Desc 1", "Thumb 1", 0.5, {}, [], 0.5),
            ClipSuggestion(30, 60, 30, "Title 2", "Desc 2", "Thumb 2", 0.8, {}, [], 0.8),
            ClipSuggestion(60, 90, 30, "Title 3", "Desc 3", "Thumb 3", 0.6, {}, [], 0.6),
        ]

        scored = self.composer._score_suggestions(suggestions)

        # Should be sorted by confidence score
        assert scored[0].confidence_score >= scored[1].confidence_score >= scored[2].confidence_score

    def test_filter_suggestions(self) -> None:
        """Test suggestion filtering."""
        suggestions = [
            ClipSuggestion(0, 30, 30, "Title 1", "Desc 1", "Thumb 1", 0.8, {}, [], 0.8),
            ClipSuggestion(30, 35, 5, "Title 2", "Desc 2", "Thumb 2", 0.7, {}, [], 0.7),  # Too short
            ClipSuggestion(60, 120, 60, "Title 3", "Desc 3", "Thumb 3", 0.6, {}, [], 0.6),  # Too long
        ]

        filtered = self.composer._filter_suggestions(suggestions, max_clips=5, min_duration=10.0, max_duration=50.0)

        assert len(filtered) == 1  # Only first suggestion meets criteria
        assert filtered[0].title == "Title 1"


class TestSmartClipComposerServiceSingleton:
    """Test singleton instance management."""

    def test_get_smart_clip_composer_service(self) -> None:
        """Test getting singleton instance."""
        composer1 = get_smart_clip_composer_service()
        composer2 = get_smart_clip_composer_service()

        # Should return same instance
        assert composer1 is composer2
        assert isinstance(composer1, SmartClipComposerService)


class TestClipSuggestion:
    """Test clip suggestion data structure."""

    def test_create_clip_suggestion(self) -> None:
        """Test creating clip suggestion."""
        suggestion = ClipSuggestion(
            start_time=10.0,
            end_time=40.0,
            duration=30.0,
            title="Amazing Tech Discussion",
            description="This is an amazing discussion about technology",
            thumbnail_text="Amazing Tech",
            confidence_score=0.85,
            signal_scores={"audio_energy": 0.8, "semantic_novelty": 0.7},
            suggested_platforms=["youtube_shorts", "tiktok"],
            estimated_engagement=0.9,
        )

        assert suggestion.start_time == 10.0
        assert suggestion.end_time == 40.0
        assert suggestion.duration == 30.0
        assert suggestion.title == "Amazing Tech Discussion"
        assert suggestion.description == "This is an amazing discussion about technology"
        assert suggestion.confidence_score == 0.85
        assert len(suggestion.signal_scores) == 2
        assert len(suggestion.suggested_platforms) == 2
        assert suggestion.estimated_engagement == 0.9

    def test_clip_suggestion_defaults(self) -> None:
        """Test clip suggestion with default values."""
        suggestion = ClipSuggestion(
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            title="Test Clip",
            description="Test description",
            thumbnail_text="Test",
            confidence_score=0.5,
        )

        assert suggestion.signal_scores == {}
        assert suggestion.suggested_platforms == []
        assert suggestion.estimated_engagement == 0.0  # Default


class TestClipVariant:
    """Test clip variant data structure."""

    def test_create_clip_variant(self) -> None:
        """Test creating clip variant."""
        variant = ClipVariant(
            variant_id="variant_1",
            title="Variant Title",
            description="Variant description",
            thumbnail_text="Variant thumbnail",
            expected_performance=0.85,
        )

        assert variant.variant_id == "variant_1"
        assert variant.title == "Variant Title"
        assert variant.description == "Variant description"
        assert variant.thumbnail_text == "Variant thumbnail"
        assert variant.expected_performance == 0.85

    def test_clip_variant_defaults(self) -> None:
        """Test clip variant with default values."""
        variant = ClipVariant(
            variant_id="variant_1",
            title="Test Variant",
            description="Test description",
            thumbnail_text="Test thumbnail",
        )

        assert variant.expected_performance == 0.0  # Default


class TestSmartClipComposerIntegration:
    """Test smart clip composer integration scenarios."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.composer = SmartClipComposerService()

    def test_generate_from_highlights(self) -> None:
        """Test clip generation from highlight detection."""
        highlights = [
            {
                "start_time": 0.0,
                "end_time": 30.0,
                "highlight_score": 0.9,
                "transcript_text": "This is an incredibly exciting moment in the discussion!",
            },
            {
                "start_time": 60.0,
                "end_time": 90.0,
                "highlight_score": 0.8,
                "transcript_text": "The guest makes an excellent point about technology.",
            },
        ]

        suggestions = self.composer._generate_from_highlights(highlights, ["youtube_shorts"])

        assert len(suggestions) == 2
        assert all(s.start_time in [0.0, 60.0] for s in suggestions)
        assert all("🎬" in s.title or "🎙️" in s.title for s in suggestions)  # Should have emojis

    def test_generate_from_transcript(self) -> None:
        """Test clip generation from transcript segments."""
        transcript_segments = [
            {
                "start_time": 0.0,
                "end_time": 30.0,
                "text": "This is a comprehensive review of the latest smartphone technology. The camera quality is outstanding and the battery life is impressive.",
            },
            {
                "start_time": 30.0,
                "end_time": 60.0,
                "text": "Short text",
            },  # Too short, should be filtered
        ]

        suggestions = self.composer._generate_from_transcript(transcript_segments, ["youtube_shorts"])

        assert len(suggestions) >= 1  # Should generate from first segment
        assert suggestions[0].start_time == 0.0
        assert suggestions[0].suggested_platforms == ["youtube_shorts"]

    def test_generate_from_topics(self) -> None:
        """Test clip generation from topic segments."""
        topic_segments = [
            {
                "start_time": 0.0,
                "end_time": 45.0,
                "transcript_text": "This is a detailed discussion about artificial intelligence and machine learning applications.",
                "topics": ["AI", "machine_learning"],
                "coherence_score": 0.85,
            },
        ]

        suggestions = self.composer._generate_from_topics(topic_segments, ["youtube_shorts"])

        assert len(suggestions) == 1
        assert suggestions[0].start_time == 0.0
        assert suggestions[0].duration == 45.0

    def test_estimate_engagement(self) -> None:
        """Test engagement estimation."""
        signal_scores = {"audio_energy": 0.8, "semantic_novelty": 0.7}
        duration = 30.0

        engagement = self.composer._estimate_engagement(signal_scores, duration)

        assert 0 <= engagement <= 1
        # Should be close to weighted average
        expected = (0.8 * 0.3) + (0.7 * 0.25)  # Using signal weights
        assert abs(engagement - expected) < 0.1

    def test_variant_generation_diverse(self) -> None:
        """Test diverse variant generation."""
        suggestion = ClipSuggestion(
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            title="🎙️ Original Title",
            description="Original description",
            thumbnail_text="Original thumbnail",
            confidence_score=0.8,
            signal_scores={},
            suggested_platforms=[],
            estimated_engagement=0.7,
        )

        variants = self.composer._generate_diverse_variants(suggestion, num_variants=2)

        assert len(variants) == 2
        # Should have different emojis/styles
        assert variants[0].title != variants[1].title

    def test_variant_generation_conservative(self) -> None:
        """Test conservative variant generation."""
        suggestion = ClipSuggestion(
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            title="Test Title",
            description="Test description",
            thumbnail_text="Test thumbnail",
            confidence_score=0.8,
            signal_scores={},
            suggested_platforms=[],
            estimated_engagement=0.7,
        )

        variants = self.composer._generate_conservative_variants(suggestion, num_variants=2)

        assert len(variants) == 2
        # Should be minor variations
        assert all("Test Title" in v.title for v in variants)

    def test_variant_generation_aggressive(self) -> None:
        """Test aggressive variant generation."""
        suggestion = ClipSuggestion(
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            title="Test Title",
            description="Test description",
            thumbnail_text="Test thumbnail",
            confidence_score=0.8,
            signal_scores={},
            suggested_platforms=[],
            estimated_engagement=0.7,
        )

        variants = self.composer._generate_aggressive_variants(suggestion, num_variants=2)

        assert len(variants) == 2
        # Should have bold modifications
        assert any("🚨" in v.title or "🔥" in v.title or "⚡" in v.title for v in variants)
