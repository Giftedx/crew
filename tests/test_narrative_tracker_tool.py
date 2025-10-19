"""
Tests for the Narrative Tracker Tool.

Tests the cross-platform narrative tracking functionality including:
- Event querying and filtering
- Timeline building
- Contradiction detection
- Insight generation
- Statistics calculation
"""

from datetime import datetime
from unittest.mock import Mock, patch

from src.kg.creator_kg_store import CreatorKGStore
from src.ultimate_discord_intelligence_bot.tools.narrative_tracker_tool import (
    NarrativeEvent,
    NarrativeTimeline,
    NarrativeTrackerInput,
    NarrativeTrackerTool,
)


class TestNarrativeTrackerInput:
    """Test the NarrativeTrackerInput schema."""

    def test_input_validation(self):
        """Test input validation with required fields."""
        input_data = NarrativeTrackerInput(
            narrative_query="Triller lawsuit", tenant="test_tenant", workspace="test_workspace"
        )

        assert input_data.narrative_query == "Triller lawsuit"
        assert input_data.creators == ["h3podcast", "hasanabi"]  # Default values
        assert input_data.tenant == "test_tenant"
        assert input_data.workspace == "test_workspace"
        assert input_data.include_cross_references is True
        assert input_data.max_events == 50

    def test_input_custom_values(self):
        """Test input with custom values."""
        input_data = NarrativeTrackerInput(
            narrative_query="Election coverage",
            creators=["h3podcast"],
            time_range={"start": "2024-01-01", "end": "2024-06-30"},
            include_cross_references=False,
            max_events=25,
            tenant="test_tenant",
            workspace="test_workspace",
        )

        assert input_data.narrative_query == "Election coverage"
        assert input_data.creators == ["h3podcast"]
        assert input_data.time_range == {"start": "2024-01-01", "end": "2024-06-30"}
        assert input_data.include_cross_references is False
        assert input_data.max_events == 25


class TestNarrativeEvent:
    """Test the NarrativeEvent dataclass."""

    def test_event_creation(self):
        """Test creating a narrative event."""
        event = NarrativeEvent(
            event_id="evt_001",
            timestamp=datetime(2024, 2, 15, 10, 30, 0),
            platform="youtube",
            content_id="video_xyz",
            creator="h3podcast",
            summary="Test event summary",
            key_claims=["claim1", "claim2"],
            quotes=[{"text": "Test quote", "speaker": "Ethan", "timestamp": 150.0}],
            contradictions=[],
            clarifications=[],
            provenance={"url": "https://example.com"},
            confidence_score=0.85,
        )

        assert event.event_id == "evt_001"
        assert event.platform == "youtube"
        assert event.creator == "h3podcast"
        assert len(event.key_claims) == 2
        assert len(event.quotes) == 1
        assert event.confidence_score == 0.85


class TestNarrativeTimeline:
    """Test the NarrativeTimeline dataclass."""

    def test_timeline_creation(self):
        """Test creating a narrative timeline."""
        events = [
            NarrativeEvent(
                event_id="evt_001",
                timestamp=datetime(2024, 2, 15, 10, 30, 0),
                platform="youtube",
                content_id="video_001",
                creator="h3podcast",
                summary="First event",
                key_claims=[],
                quotes=[],
                contradictions=[],
                clarifications=[],
                provenance={},
                confidence_score=0.85,
            )
        ]

        timeline = NarrativeTimeline(
            narrative_id="narrative_test",
            narrative_query="Test narrative",
            timeline=events,
            statistics={"total_events": 1},
            contradictions=[],
            key_insights=["Test insight"],
        )

        assert timeline.narrative_id == "narrative_test"
        assert timeline.narrative_query == "Test narrative"
        assert len(timeline.timeline) == 1
        assert timeline.statistics["total_events"] == 1
        assert len(timeline.key_insights) == 1


class TestNarrativeTrackerTool:
    """Test the NarrativeTrackerTool class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_kg_store = Mock(spec=CreatorKGStore)
        self.tool = NarrativeTrackerTool(kg_store=self.mock_kg_store)

    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "narrative_tracker_tool"
        assert "Track narratives across platforms" in self.tool.description
        assert self.tool.args_schema == NarrativeTrackerInput

    def test_tool_initialization_without_kg_store(self):
        """Test tool initialization without KG store."""
        tool = NarrativeTrackerTool()
        assert tool.kg_store is not None

    def test_run_success(self):
        """Test successful narrative tracking."""
        result = self.tool._run(
            narrative_query="Triller lawsuit",
            creators=["h3podcast", "hasanabi"],
            time_range={"start": "2024-01-01", "end": "2024-12-31"},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        assert result.success
        assert "data" in result.data
        data = result.data["data"]

        assert "narrative_id" in data
        assert "timeline" in data
        assert "statistics" in data
        assert "contradictions" in data
        assert "key_insights" in data

        # Check that we got some events
        assert len(data["timeline"]) > 0
        assert data["statistics"]["total_events"] > 0

    def test_run_no_events_found(self):
        """Test narrative tracking when no events are found."""
        # Mock the query to return no events
        with patch.object(self.tool, "_query_narrative_events", return_value=[]):
            result = self.tool._run(
                narrative_query="Non-existent narrative",
                creators=["unknown_creator"],
                time_range={"start": "2024-01-01", "end": "2024-12-31"},
                tenant="test_tenant",
                workspace="test_workspace",
            )

            assert result.success
            data = result.data["data"]
            assert data["statistics"]["total_events"] == 0
            assert len(data["timeline"]) == 0
            assert "No events found" in data["key_insights"][0]

    def test_run_with_time_filtering(self):
        """Test narrative tracking with time range filtering."""
        result = self.tool._run(
            narrative_query="Triller lawsuit",
            creators=["h3podcast"],
            time_range={"start": "2024-02-01", "end": "2024-02-28"},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        assert result.success
        data = result.data["data"]

        # All events should be within the specified time range
        for event in data["timeline"]:
            event_date = datetime.fromisoformat(event["timestamp"])
            assert event_date >= datetime(2024, 2, 1)
            assert event_date <= datetime(2024, 2, 28)

    def test_run_with_max_events_limit(self):
        """Test narrative tracking with max events limit."""
        result = self.tool._run(
            narrative_query="Triller lawsuit",
            creators=["h3podcast", "hasanabi"],
            time_range={"start": "2024-01-01", "end": "2024-12-31"},
            max_events=2,
            tenant="test_tenant",
            workspace="test_workspace",
        )

        assert result.success
        data = result.data["data"]
        assert len(data["timeline"]) <= 2

    def test_query_narrative_events(self):
        """Test querying narrative events."""
        events = self.tool._query_narrative_events(
            narrative_query="Triller lawsuit",
            creators=["h3podcast"],
            time_range={"start": "2024-01-01", "end": "2024-12-31"},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        assert isinstance(events, list)
        if events:  # If mock data is returned
            event = events[0]
            assert "event_id" in event
            assert "timestamp" in event
            assert "platform" in event
            assert "creator" in event
            assert "summary" in event

    def test_build_timeline(self):
        """Test building timeline from events."""
        mock_events = [
            {
                "event_id": "evt_002",
                "timestamp": datetime(2024, 2, 16, 14, 20, 0),
                "platform": "twitch",
                "content_id": "vod_002",
                "creator": "hasanabi",
                "summary": "Second event",
                "key_claims": ["claim2"],
                "quotes": [{"text": "Quote 2", "speaker": "Hasan", "timestamp": 200.0}],
                "topics": ["topic2"],
                "url": "https://twitch.tv/videos/002",
                "episode_title": "Hasan Reacts to H3",
            },
            {
                "event_id": "evt_001",
                "timestamp": datetime(2024, 2, 15, 10, 30, 0),
                "platform": "youtube",
                "content_id": "video_001",
                "creator": "h3podcast",
                "summary": "First event",
                "key_claims": ["claim1"],
                "quotes": [{"text": "Quote 1", "speaker": "Ethan", "timestamp": 150.0}],
                "topics": ["topic1"],
                "url": "https://youtube.com/watch?v=001",
                "episode_title": "H3 Podcast #123",
            },
        ]

        timeline = self.tool._build_timeline(mock_events, max_events=10)

        assert len(timeline) == 2
        # Should be sorted by timestamp
        assert timeline[0].event_id == "evt_001"  # Earlier timestamp
        assert timeline[1].event_id == "evt_002"  # Later timestamp

        # Check event structure
        event = timeline[0]
        assert isinstance(event, NarrativeEvent)
        assert event.event_id == "evt_001"
        assert event.platform == "youtube"
        assert event.creator == "h3podcast"

    def test_build_timeline_with_max_events(self):
        """Test building timeline with max events limit."""
        mock_events = [
            {
                "event_id": f"evt_{i:03d}",
                "timestamp": datetime(2024, 2, 15 + i, 10, 30, 0),
                "platform": "youtube",
                "content_id": f"video_{i:03d}",
                "creator": "h3podcast",
                "summary": f"Event {i}",
                "key_claims": [f"claim{i}"],
                "quotes": [{"text": f"Quote {i}", "speaker": "Ethan", "timestamp": 150.0}],
                "topics": [f"topic{i}"],
                "url": f"https://youtube.com/watch?v={i:03d}",
                "episode_title": f"H3 Podcast #{123 + i}",
            }
            for i in range(5)
        ]

        timeline = self.tool._build_timeline(mock_events, max_events=3)

        assert len(timeline) == 3  # Should be limited to 3 events

    def test_identify_contradictions(self):
        """Test contradiction identification."""
        events = [
            NarrativeEvent(
                event_id="evt_001",
                timestamp=datetime(2024, 2, 15, 10, 30, 0),
                platform="youtube",
                content_id="video_001",
                creator="h3podcast",
                summary="Optimistic about lawsuit",
                key_claims=["We will win this lawsuit", "I'm confident"],
                quotes=[],
                contradictions=[],
                clarifications=[],
                provenance={},
                confidence_score=0.85,
            ),
            NarrativeEvent(
                event_id="evt_002",
                timestamp=datetime(2024, 2, 16, 14, 20, 0),
                platform="twitch",
                content_id="vod_002",
                creator="hasanabi",
                summary="Pessimistic about lawsuit",
                key_claims=["Ethan is too optimistic", "This might fail"],
                quotes=[],
                contradictions=[],
                clarifications=[],
                provenance={},
                confidence_score=0.85,
            ),
        ]

        contradictions = self.tool._identify_contradictions(events)

        assert len(contradictions) > 0
        contradiction = contradictions[0]
        assert "event1_id" in contradiction
        assert "event2_id" in contradiction
        assert "description" in contradiction
        assert "confidence" in contradiction

    def test_claims_contradict(self):
        """Test claim contradiction detection."""
        # Positive vs negative claims
        claims1 = ["We will win this lawsuit", "I'm confident"]
        claims2 = ["This might fail", "I'm concerned"]

        assert self.tool._claims_contradict(claims1, claims2) is True

        # Both positive claims
        claims3 = ["We will win", "I'm confident"]
        claims4 = ["This will succeed", "I'm optimistic"]

        assert self.tool._claims_contradict(claims3, claims4) is False

        # Both negative claims
        claims5 = ["This might fail", "I'm concerned"]
        claims6 = ["This will lose", "I'm pessimistic"]

        assert self.tool._claims_contradict(claims5, claims6) is False

    def test_generate_insights(self):
        """Test insight generation."""
        events = [
            NarrativeEvent(
                event_id="evt_001",
                timestamp=datetime(2024, 2, 15, 10, 30, 0),
                platform="youtube",
                content_id="video_001",
                creator="h3podcast",
                summary="First event",
                key_claims=["claim1"],
                quotes=[{"text": "Quote 1", "speaker": "Ethan", "timestamp": 150.0}],
                contradictions=[],
                clarifications=[],
                provenance={},
                confidence_score=0.85,
            ),
            NarrativeEvent(
                event_id="evt_002",
                timestamp=datetime(2024, 2, 20, 14, 20, 0),
                platform="twitch",
                content_id="vod_002",
                creator="hasanabi",
                summary="Second event",
                key_claims=["claim2"],
                quotes=[{"text": "Quote 2", "speaker": "Hasan", "timestamp": 200.0}],
                contradictions=[],
                clarifications=[],
                provenance={},
                confidence_score=0.85,
            ),
        ]

        contradictions = []
        insights = self.tool._generate_insights(events, contradictions)

        assert len(insights) > 0
        assert any("spans" in insight and "days" in insight for insight in insights)
        assert any("Active creators" in insight for insight in insights)
        assert any("Platforms involved" in insight for insight in insights)
        assert any("quotes extracted" in insight for insight in insights)

    def test_calculate_statistics(self):
        """Test statistics calculation."""
        events = [
            NarrativeEvent(
                event_id="evt_001",
                timestamp=datetime(2024, 2, 15, 10, 30, 0),
                platform="youtube",
                content_id="video_001",
                creator="h3podcast",
                summary="First event",
                key_claims=[],
                quotes=[],
                contradictions=[],
                clarifications=[],
                provenance={},
                confidence_score=0.85,
            ),
            NarrativeEvent(
                event_id="evt_002",
                timestamp=datetime(2024, 2, 16, 14, 20, 0),
                platform="twitch",
                content_id="vod_002",
                creator="hasanabi",
                summary="Second event",
                key_claims=[],
                quotes=[],
                contradictions=[],
                clarifications=[],
                provenance={},
                confidence_score=0.85,
            ),
        ]

        creators = ["h3podcast", "hasanabi"]
        stats = self.tool._calculate_statistics(events, creators)

        assert stats["total_events"] == 2
        assert "youtube" in stats["platforms"]
        assert "twitch" in stats["platforms"]
        assert "h3podcast" in stats["events_per_creator"]
        assert "hasanabi" in stats["events_per_creator"]
        assert stats["events_per_creator"]["h3podcast"] == 1
        assert stats["events_per_creator"]["hasanabi"] == 1

    def test_calculate_statistics_empty_timeline(self):
        """Test statistics calculation with empty timeline."""
        events = []
        creators = ["h3podcast", "hasanabi"]
        stats = self.tool._calculate_statistics(events, creators)

        assert stats["total_events"] == 0
        assert stats["platforms"] == []
        assert stats["date_range"]["first"] is None
        assert stats["date_range"]["last"] is None
        assert stats["creators"] == creators

    def test_serialize_timeline(self):
        """Test timeline serialization."""
        events = [
            NarrativeEvent(
                event_id="evt_001",
                timestamp=datetime(2024, 2, 15, 10, 30, 0),
                platform="youtube",
                content_id="video_001",
                creator="h3podcast",
                summary="Test event",
                key_claims=["claim1"],
                quotes=[{"text": "Test quote", "speaker": "Ethan", "timestamp": 150.0}],
                contradictions=[],
                clarifications=[],
                provenance={"url": "https://example.com"},
                confidence_score=0.85,
            )
        ]

        timeline = NarrativeTimeline(
            narrative_id="narrative_test",
            narrative_query="Test narrative",
            timeline=events,
            statistics={"total_events": 1},
            contradictions=[],
            key_insights=["Test insight"],
        )

        serialized = self.tool._serialize_timeline(timeline)

        assert serialized["narrative_id"] == "narrative_test"
        assert serialized["narrative_query"] == "Test narrative"
        assert len(serialized["timeline"]) == 1
        assert serialized["statistics"]["total_events"] == 1

        # Check event serialization
        event = serialized["timeline"][0]
        assert event["event_id"] == "evt_001"
        assert event["timestamp"] == "2024-02-15T10:30:00"
        assert event["platform"] == "youtube"
        assert event["creator"] == "h3podcast"
        assert event["confidence_score"] == 0.85

    def test_run_exception_handling(self):
        """Test exception handling in _run method."""
        # Mock _query_narrative_events to raise an exception
        with patch.object(self.tool, "_query_narrative_events", side_effect=Exception("Test error")):
            result = self.tool._run(
                narrative_query="Test narrative",
                creators=["h3podcast"],
                time_range={"start": "2024-01-01", "end": "2024-12-31"},
                tenant="test_tenant",
                workspace="test_workspace",
            )

            assert not result.success
            assert "Narrative tracking failed" in result.error
            assert "Test error" in result.error
