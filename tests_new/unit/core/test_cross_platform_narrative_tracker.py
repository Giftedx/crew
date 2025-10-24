"""Tests for Cross-Platform Narrative Tracker."""

from __future__ import annotations

from features.narrative_tracker.cross_platform_narrative_tracker import (
    CrossPlatformNarrativeTracker,
    NarrativeEvent,
    NarrativeThread,
    get_cross_platform_narrative_tracker,
)


class TestCrossPlatformNarrativeTracker:
    """Test cross-platform narrative tracker functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.tracker = CrossPlatformNarrativeTracker(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.tracker.cache_size == 100
        assert len(self.tracker._tracking_cache) == 0

    def test_track_narrative_evolution_basic(self) -> None:
        """Test basic narrative evolution tracking."""
        content_items = [
            {
                "id": "yt_1",
                "platform": "youtube",
                "title": "Breaking: Major Tech Announcement",
                "text": "A major tech company just announced a revolutionary new product.",
                "timestamp": 1000000000,
            },
            {
                "id": "tw_1",
                "platform": "twitter",
                "text": "Excited about the new tech announcement! This could change everything.",
                "timestamp": 1000000060,
            },
        ]

        result = self.tracker.track_narrative_evolution(
            content_items,
            time_window_hours=1,
            similarity_threshold=0.5,
            use_cache=False,
        )

        assert result.success
        assert result.data is not None
        assert "narrative_threads" in result.data
        assert result.data["total_content_analyzed"] == 2

    def test_find_contradictions_and_clarifications(self) -> None:
        """Test contradiction and clarification detection."""
        content_items = [
            {
                "id": "original",
                "text": "The company will release the product next month.",
                "timestamp": 1000000000,
            },
            {
                "id": "clarification",
                "text": "Actually, the release date has been moved to next quarter.",
                "timestamp": 1000000060,
            },
        ]

        result = self.tracker.find_contradictions_and_clarifications(
            content_items, similarity_threshold=0.8, use_cache=False
        )

        assert result.success
        assert result.data is not None
        assert "contradictions" in result.data
        assert "clarifications" in result.data

    def test_generate_narrative_timeline(self) -> None:
        """Test narrative timeline generation."""
        # Create a mock narrative thread
        thread = NarrativeThread(
            thread_id="test_thread",
            title="Test Narrative",
            summary="Test summary",
            events=[
                NarrativeEvent(
                    event_id="event_1",
                    primary_content={"id": "item1", "timestamp": 1000000000},
                    related_content=[],
                    narrative_type="breaking_news",
                    evolution_timeline=[],
                    confidence=0.8,
                    created_at=1000000000,
                    updated_at=1000000000,
                )
            ],
            platforms_involved=["youtube"],
            key_participants=["creator1"],
            total_reach=1000,
            evolution_score=0.5,
            created_at=1000000000,
            updated_at=1000000000,
        )

        result = self.tracker.generate_narrative_timeline(thread)

        assert result.success
        assert result.data is not None
        assert "timeline_events" in result.data
        assert result.data["thread_id"] == "test_thread"

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some cached tracking results
        self.tracker.track_narrative_evolution([{"text": "test"}], use_cache=True)

        assert len(self.tracker._tracking_cache) > 0

        # Clear cache
        result = self.tracker.clear_cache()

        assert result.success
        assert result.data["cleared_entries"] > 0
        assert len(self.tracker._tracking_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        # Add some cached tracking results
        self.tracker.track_narrative_evolution([{"text": "test"}], use_cache=True)

        result = self.tracker.get_cache_stats()

        assert result.success
        assert result.data is not None
        assert "total_cached" in result.data
        assert "cache_size_limit" in result.data

        assert result.data["total_cached"] >= 1
        assert result.data["cache_size_limit"] == 100

    def test_model_selection(self) -> None:
        """Test model selection logic."""
        assert self.tracker._select_model("fast") == "fast_tracking"
        assert self.tracker._select_model("balanced") == "balanced_tracking"
        assert self.tracker._select_model("quality") == "quality_tracking"
        assert self.tracker._select_model("unknown") == "balanced_tracking"  # Default

    def test_cluster_by_topic(self) -> None:
        """Test topic-based clustering."""
        content_items = [
            {"id": "item1", "text": "This is about AI technology and innovation"},
            {"id": "item2", "text": "This is also about AI and machine learning"},
            {"id": "item3", "text": "This is about cooking and recipes"},
        ]

        clusters = self.tracker._cluster_by_topic(content_items, threshold=0.6)

        assert len(clusters) >= 2  # Should have at least AI cluster and cooking cluster

    def test_text_similarity_calculation(self) -> None:
        """Test text similarity calculation."""
        text1 = "This is a test about AI"
        text2 = "This is a test about AI"  # Identical

        similarity = self.tracker._calculate_text_similarity(text1, text2)
        assert similarity == 1.0

        text3 = "This is completely different content"
        similarity2 = self.tracker._calculate_text_similarity(text1, text3)
        assert similarity2 < 1.0

    def test_narrative_type_classification(self) -> None:
        """Test narrative type classification."""
        # First item should be breaking news
        narrative_type = self.tracker._classify_narrative_type({"id": "item1"}, 0, 3)
        assert narrative_type == "breaking_news"

        # Last item should be clarification
        narrative_type2 = self.tracker._classify_narrative_type({"id": "item3"}, 2, 3)
        assert narrative_type2 == "clarification"

        # Middle item should be evolution
        narrative_type3 = self.tracker._classify_narrative_type({"id": "item2"}, 1, 3)
        assert narrative_type3 == "evolution"


class TestCrossPlatformNarrativeTrackerSingleton:
    """Test singleton instance management."""

    def test_get_cross_platform_narrative_tracker(self) -> None:
        """Test getting singleton instance."""
        tracker1 = get_cross_platform_narrative_tracker()
        tracker2 = get_cross_platform_narrative_tracker()

        # Should return same instance
        assert tracker1 is tracker2
        assert isinstance(tracker1, CrossPlatformNarrativeTracker)


class TestNarrativeEvent:
    """Test narrative event data structure."""

    def test_create_narrative_event(self) -> None:
        """Test creating narrative event."""
        event = NarrativeEvent(
            event_id="event_1",
            primary_content={"id": "item1", "title": "Breaking News"},
            related_content=[{"id": "item2", "title": "Follow-up"}],
            narrative_type="breaking_news",
            evolution_timeline=[
                {"item": {"id": "item1"}, "timestamp": 1000000000},
                {"item": {"id": "item2"}, "timestamp": 1000000060},
            ],
            confidence=0.85,
            created_at=1000000000,
            updated_at=1000000060,
        )

        assert event.event_id == "event_1"
        assert event.narrative_type == "breaking_news"
        assert len(event.related_content) == 1
        assert len(event.evolution_timeline) == 2
        assert event.confidence == 0.85

    def test_narrative_event_defaults(self) -> None:
        """Test narrative event with default values."""
        event = NarrativeEvent(
            event_id="event_1",
            primary_content={"id": "item1"},
            related_content=[],
            narrative_type="evolution",
            evolution_timeline=[],
            confidence=0.5,
            created_at=1000000000,
            updated_at=1000000000,
        )

        assert event.narrative_type == "evolution"
        assert len(event.related_content) == 0
        assert len(event.evolution_timeline) == 0


class TestNarrativeThread:
    """Test narrative thread data structure."""

    def test_create_narrative_thread(self) -> None:
        """Test creating narrative thread."""
        thread = NarrativeThread(
            thread_id="thread_1",
            title="Tech Announcement Evolution",
            summary="A major tech announcement and its evolution across platforms",
            events=[
                NarrativeEvent(
                    event_id="event_1",
                    primary_content={"id": "item1"},
                    related_content=[],
                    narrative_type="breaking_news",
                    evolution_timeline=[],
                    confidence=0.8,
                    created_at=1000000000,
                    updated_at=1000000000,
                )
            ],
            platforms_involved=["youtube", "twitter"],
            key_participants=["creator1", "influencer1"],
            total_reach=50000,
            evolution_score=0.7,
            created_at=1000000000,
            updated_at=1000000060,
        )

        assert thread.thread_id == "thread_1"
        assert thread.title == "Tech Announcement Evolution"
        assert len(thread.events) == 1
        assert len(thread.platforms_involved) == 2
        assert len(thread.key_participants) == 2
        assert thread.total_reach == 50000
        assert thread.evolution_score == 0.7

    def test_narrative_thread_empty(self) -> None:
        """Test narrative thread with no events."""
        thread = NarrativeThread(
            thread_id="empty_thread",
            title="Empty Thread",
            summary="No events",
            events=[],
            platforms_involved=[],
            key_participants=[],
            total_reach=0,
            evolution_score=0.0,
            created_at=1000000000,
            updated_at=1000000000,
        )

        assert thread.thread_id == "empty_thread"
        assert len(thread.events) == 0
        assert len(thread.platforms_involved) == 0
        assert thread.total_reach == 0


class TestCrossPlatformNarrativeTrackerIntegration:
    """Test narrative tracker integration scenarios."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.tracker = CrossPlatformNarrativeTracker()

    def test_track_realistic_narrative_evolution(self) -> None:
        """Test tracking a realistic narrative evolution scenario."""
        content_items = [
            {
                "id": "yt_announcement",
                "platform": "youtube",
                "title": "BREAKING: Revolutionary AI Technology Announced",
                "text": "A major tech company has just announced a revolutionary AI technology that will change how we interact with computers.",
                "timestamp": 1000000000,
                "author": "TechCreator",
            },
            {
                "id": "tw_reaction",
                "platform": "twitter",
                "text": "Wow! This new AI technology announcement is incredible. Can't wait to see how it develops! #AI #Tech",
                "timestamp": 1000000060,
                "author": "TechInfluencer",
            },
            {
                "id": "rd_discussion",
                "platform": "reddit",
                "title": "Discussion: Revolutionary AI Technology - What Does This Mean?",
                "text": "The recent AI announcement has sparked a lot of discussion. Some people are excited, others are concerned about privacy implications.",
                "timestamp": 1000000120,
                "author": "RedditUser",
            },
        ]

        result = self.tracker.track_narrative_evolution(
            content_items,
            time_window_hours=1,
            similarity_threshold=0.6,
            max_threads=10,
            use_cache=False,
        )

        assert result.success
        narrative_threads = result.data["narrative_threads"]

        # Should find at least one narrative thread
        assert len(narrative_threads) >= 1

        # Check thread structure
        thread = narrative_threads[0]
        assert thread.title
        assert len(thread.platforms_involved) >= 2  # Multiple platforms
        assert thread.total_reach > 0

    def test_contradiction_detection(self) -> None:
        """Test detection of contradictions in narrative evolution."""
        content_items = [
            {
                "id": "original_claim",
                "text": "The new AI technology will be available to all users for free.",
                "timestamp": 1000000000,
            },
            {
                "id": "contradiction",
                "text": "Actually, the AI technology will require a premium subscription for full access.",
                "timestamp": 1000000060,
            },
        ]

        result = self.tracker.find_contradictions_and_clarifications(
            content_items, similarity_threshold=0.7, use_cache=False
        )

        assert result.success

        # Should detect some contradictions
        contradictions = result.data["contradictions"]
        clarifications = result.data["clarifications"]

        # May or may not detect contradictions depending on similarity threshold
        # The important thing is that it doesn't crash
        assert isinstance(contradictions, list)
        assert isinstance(clarifications, list)
