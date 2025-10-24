import json
from unittest.mock import Mock

from src.ultimate_discord_intelligence_bot.tools.smart_clip_composer_tool import (
    ClipSuggestion,
    ExportData,
    SmartClipComposerInput,
    SmartClipComposerTool,
)


class TestSmartClipComposerInput:
    """Test the SmartClipComposerInput schema."""

    def test_valid_input(self):
        """Test valid input creation."""
        input_data = SmartClipComposerInput(
            episode_id="episode_123",
            max_clips=5,
            min_clip_length=30.0,
            max_clip_length=90.0,
            highlight_threshold=0.7,
            include_titles=True,
            export_formats=["json", "xml"],
        )

        assert input_data.episode_id == "episode_123"
        assert input_data.max_clips == 5
        assert input_data.min_clip_length == 30.0
        assert input_data.max_clip_length == 90.0
        assert input_data.highlight_threshold == 0.7
        assert input_data.include_titles is True
        assert input_data.export_formats == ["json", "xml"]

    def test_default_values(self):
        """Test default values."""
        input_data = SmartClipComposerInput(episode_id="episode_123")

        assert input_data.episode_id == "episode_123"
        assert input_data.max_clips == 10
        assert input_data.min_clip_length == 15.0
        assert input_data.max_clip_length == 120.0
        assert input_data.highlight_threshold == 0.6
        assert input_data.include_titles is True
        assert input_data.export_formats == ["json"]


class TestClipSuggestion:
    """Test the ClipSuggestion dataclass."""

    def test_clip_suggestion_creation(self):
        """Test creating a ClipSuggestion."""
        clip = ClipSuggestion(
            clip_id="clip_001",
            start_time=300.0,
            end_time=420.0,
            duration=120.0,
            highlight_score=0.85,
            proposed_title="Ethan Reacts to Triller News",
            title_variants=["Title 1", "Title 2", "Title 3"],
            reasoning="High audio energy and visual reaction",
            signals={"audio_novelty": 0.8, "semantic_novelty": 0.9},
            thumbnail_frame_time=360.0,
            content_summary="Ethan discusses lawsuit...",
            tags=["legal", "reaction"],
        )

        assert clip.clip_id == "clip_001"
        assert clip.start_time == 300.0
        assert clip.end_time == 420.0
        assert clip.duration == 120.0
        assert clip.highlight_score == 0.85
        assert clip.proposed_title == "Ethan Reacts to Triller News"
        assert clip.title_variants == ["Title 1", "Title 2", "Title 3"]
        assert clip.reasoning == "High audio energy and visual reaction"
        assert clip.signals == {"audio_novelty": 0.8, "semantic_novelty": 0.9}
        assert clip.thumbnail_frame_time == 360.0
        assert clip.content_summary == "Ethan discusses lawsuit..."
        assert clip.tags == ["legal", "reaction"]


class TestExportData:
    """Test the ExportData dataclass."""

    def test_export_data_creation(self):
        """Test creating ExportData."""
        export = ExportData(
            format_name="json",
            content='{"test": "data"}',
            filename="clips_episode123.json",
        )

        assert export.format_name == "json"
        assert export.content == '{"test": "data"}'
        assert export.filename == "clips_episode123.json"


class TestSmartClipComposerTool:
    """Test the SmartClipComposerTool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = SmartClipComposerTool()
        self.tenant = "test_tenant"
        self.workspace = "test_workspace"
        self.episode_id = "episode_123"

    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "smart_clip_composer_tool"
        assert "Analyze episodes for highlight-worthy moments" in self.tool.description
        assert self.tool.args_schema == SmartClipComposerInput

    def test_retrieve_episode_data(self):
        """Test episode data retrieval."""
        data = self.tool._retrieve_episode_data(self.episode_id, self.tenant, self.workspace)

        assert data is not None
        assert data["episode_id"] == self.episode_id
        assert "title" in data
        assert "duration" in data
        assert "transcript_segments" in data
        assert len(data["transcript_segments"]) > 0

    def test_calculate_audio_score(self):
        """Test audio score calculation."""
        segment_high_energy = {
            "energy_level": 0.8,
            "sentiment": "excited",
        }
        score_high = self.tool._calculate_audio_score(segment_high_energy)
        assert score_high > 0.7

        segment_low_energy = {
            "energy_level": 0.3,
            "sentiment": "neutral",
        }
        score_low = self.tool._calculate_audio_score(segment_low_energy)
        assert score_low < 0.6

    def test_calculate_semantic_score(self):
        """Test semantic score calculation."""
        segment_important = {
            "start_time": 300.0,
            "end_time": 420.0,
            "topic": "legal",
            "claims": [{"timestamp": 350.0}],
        }
        score_important = self.tool._calculate_semantic_score(segment_important)
        assert score_important > 0.7

        segment_unimportant = {
            "start_time": 300.0,
            "end_time": 420.0,
            "topic": "general",
            "claims": [],
        }
        score_unimportant = self.tool._calculate_semantic_score(segment_unimportant)
        assert score_unimportant < 0.6

    def test_calculate_visual_score(self):
        """Test visual score calculation."""
        segment = {"start_time": 300.0, "end_time": 420.0}
        visual_events = [
            {"timestamp": 350.0, "intensity": 0.8},
        ]
        score = self.tool._calculate_visual_score(segment, visual_events)
        assert score > 0.7

        # Test without visual events
        score_no_events = self.tool._calculate_visual_score(segment, [])
        assert score_no_events == 0.3

    def test_calculate_engagement_score(self):
        """Test engagement score calculation."""
        segment = {"start_time": 300.0, "end_time": 420.0}
        chat_spikes = [
            {"timestamp": 350.0, "velocity": 15},
        ]
        score = self.tool._calculate_engagement_score(segment, chat_spikes)
        assert score > 0.7

        # Test without chat spikes
        score_no_spikes = self.tool._calculate_engagement_score(segment, [])
        assert score_no_spikes == 0.2

    def test_generate_reasoning(self):
        """Test reasoning generation."""
        segment = {
            "energy_level": 0.8,
            "sentiment": "excited",
            "topic": "legal",
        }
        reasoning = self.tool._generate_reasoning(segment, 0.85)
        assert "high audio energy" in reasoning
        assert "strong emotional reaction" in reasoning
        assert "important topic" in reasoning
        assert "0.85" in reasoning

    def test_generate_title_variants(self):
        """Test title variant generation."""
        segment = {"speaker": "Ethan", "topic": "legal"}
        episode_data = {"title": "H3 Podcast #123 - Triller Lawsuit Discussion"}

        variants = self.tool._generate_title_variants(segment, episode_data)

        assert len(variants) > 0
        assert any("Ethan" in variant for variant in variants)
        assert any("legal" in variant.lower() for variant in variants)

    def test_generate_clip_tags(self):
        """Test clip tag generation."""
        segment = {
            "topic": "legal",
            "sentiment": "excited",
            "speaker": "Ethan",
        }

        tags = self.tool._generate_clip_tags(segment)

        assert "legal" in tags
        assert "excited" in tags
        assert "speaker:Ethan" in tags
        assert "highlight" in tags
        assert "clip" in tags
        assert "viral" in tags

    def test_export_json(self):
        """Test JSON export."""
        clips = [
            ClipSuggestion(
                clip_id="clip_001",
                start_time=300.0,
                end_time=420.0,
                duration=120.0,
                highlight_score=0.85,
                proposed_title="Test Clip",
                title_variants=["Title 1"],
                reasoning="Test reasoning",
                signals={"audio": 0.8},
                thumbnail_frame_time=360.0,
                content_summary="Test content",
                tags=["test"],
            )
        ]

        json_content = self.tool._export_json(clips, self.episode_id)

        # Verify it's valid JSON
        data = json.loads(json_content)
        assert data["episode_id"] == self.episode_id
        assert len(data["clip_suggestions"]) == 1
        assert data["clip_suggestions"][0]["clip_id"] == "clip_001"

    def test_export_xml(self):
        """Test XML export."""
        clips = [
            ClipSuggestion(
                clip_id="clip_001",
                start_time=300.0,
                end_time=420.0,
                duration=120.0,
                highlight_score=0.85,
                proposed_title="Test Clip",
                title_variants=[],
                reasoning="",
                signals={},
                thumbnail_frame_time=360.0,
                content_summary="",
                tags=[],
            )
        ]

        xml_content = self.tool._export_xml(clips, self.episode_id)

        assert '<?xml version="1.0"' in xml_content
        assert "<PremiereClipExport>" in xml_content
        assert self.episode_id in xml_content
        assert "clip_001" in xml_content
        assert "</PremiereClipExport>" in xml_content

    def test_export_csv(self):
        """Test CSV export."""
        clips = [
            ClipSuggestion(
                clip_id="clip_001",
                start_time=300.0,
                end_time=420.0,
                duration=120.0,
                highlight_score=0.85,
                proposed_title="Test Clip",
                title_variants=[],
                reasoning="",
                signals={},
                thumbnail_frame_time=360.0,
                content_summary="",
                tags=["legal", "reaction"],
            )
        ]

        csv_content = self.tool._export_csv(clips, self.episode_id)

        lines = csv_content.strip().split("\n")
        assert len(lines) == 2  # Header + 1 data line
        assert "ClipID,StartTime,EndTime,Duration,Title,HighlightScore,Tags" in lines[0]
        assert "clip_001" in lines[1]
        assert "300.0" in lines[1]
        assert "420.0" in lines[1]
        assert "Test Clip" in lines[1]
        assert "0.85" in lines[1]

    def test_run_success(self):
        """Test successful clip composition."""
        result = self.tool._run(
            episode_id=self.episode_id,
            max_clips=5,
            highlight_threshold=0.5,
            export_formats=["json"],
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert result.success
        data = result.data["data"]
        assert data["episode_id"] == self.episode_id
        assert "clip_suggestions" in data
        assert "total_clips" in data
        assert "export_formats" in data
        assert "summary" in data
        assert len(data["clip_suggestions"]) > 0

    def test_run_with_titles(self):
        """Test clip composition with title generation."""
        result = self.tool._run(
            episode_id=self.episode_id,
            max_clips=3,
            include_titles=True,
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert result.success
        clips = result.data["data"]["clip_suggestions"]
        for clip in clips:
            assert "proposed_title" in clip
            assert "title_variants" in clip
            assert len(clip["title_variants"]) > 0

    def test_run_multiple_exports(self):
        """Test clip composition with multiple export formats."""
        result = self.tool._run(
            episode_id=self.episode_id,
            export_formats=["json", "xml", "csv"],
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert result.success
        exports = result.data["data"]["export_formats"]
        assert "json" in exports
        assert "xml" in exports
        assert "csv" in exports

    def test_run_episode_not_found(self):
        """Test handling of non-existent episode."""
        # Mock the retrieve method to return None
        original_method = self.tool._retrieve_episode_data
        self.tool._retrieve_episode_data = Mock(return_value=None)

        try:
            result = self.tool._run(
                episode_id="nonexistent_episode",
                tenant=self.tenant,
                workspace=self.workspace,
            )

            assert not result.success
            assert "not found" in result.error.lower()
        finally:
            # Restore original method
            self.tool._retrieve_episode_data = original_method

    def test_serialize_clip_suggestion(self):
        """Test clip suggestion serialization."""
        clip = ClipSuggestion(
            clip_id="clip_001",
            start_time=300.0,
            end_time=420.0,
            duration=120.0,
            highlight_score=0.85,
            proposed_title="Test Clip",
            title_variants=["Title 1", "Title 2"],
            reasoning="Test reasoning",
            signals={"audio": 0.8, "visual": 0.7},
            thumbnail_frame_time=360.0,
            content_summary="Test content summary",
            tags=["tag1", "tag2"],
        )

        serialized = self.tool._serialize_clip_suggestion(clip)

        assert serialized["clip_id"] == "clip_001"
        assert serialized["start_time"] == 300.0
        assert serialized["end_time"] == 420.0
        assert serialized["duration"] == 120.0
        assert serialized["highlight_score"] == 0.85
        assert serialized["proposed_title"] == "Test Clip"
        assert serialized["title_variants"] == ["Title 1", "Title 2"]
        assert serialized["reasoning"] == "Test reasoning"
        assert serialized["signals"] == {"audio": 0.8, "visual": 0.7}
        assert serialized["thumbnail_frame_time"] == 360.0
        assert serialized["content_summary"] == "Test content summary"
        assert serialized["tags"] == ["tag1", "tag2"]

    def test_analyze_highlights(self):
        """Test highlight analysis."""
        episode_data = {
            "episode_id": self.episode_id,
            "transcript_segments": [
                {
                    "start_time": 300.0,
                    "end_time": 420.0,
                    "text": "High energy segment",
                    "speaker": "Ethan",
                    "sentiment": "excited",
                    "energy_level": 0.8,
                    "topic": "legal",
                },
                {
                    "start_time": 600.0,
                    "end_time": 720.0,
                    "text": "Low energy segment",
                    "speaker": "Guest",
                    "sentiment": "neutral",
                    "energy_level": 0.3,
                    "topic": "general",
                },
            ],
            "visual_events": [
                {"timestamp": 350.0, "intensity": 0.8},
            ],
            "chat_spikes": [
                {"timestamp": 320.0, "velocity": 15},
            ],
        }

        highlights = self.tool._analyze_highlights(episode_data)

        assert len(highlights) > 0
        # First segment should have high score
        high_score_segment = next(h for h in highlights if h["start_time"] == 300.0)
        assert high_score_segment["highlight_score"] > 0.7
        assert "signals" in high_score_segment
        assert "reasoning" in high_score_segment

    def test_generate_clip_suggestions(self):
        """Test clip suggestion generation."""
        highlight_segments = [
            {
                "start_time": 300.0,
                "end_time": 420.0,
                "highlight_score": 0.8,
                "signals": {"audio": 0.8, "semantic": 0.7},
                "reasoning": "High energy",
                "speaker": "Ethan",
                "topic": "legal",
                "text": "Test content",
            }
        ]

        episode_data = {
            "episode_id": self.episode_id,
            "title": "Test Episode",
            "duration": 5400,
        }

        suggestions = self.tool._generate_clip_suggestions(
            highlight_segments,
            episode_data,
            max_clips=5,
            min_clip_length=15.0,
            max_clip_length=120.0,
            highlight_threshold=0.6,
            include_titles=True,
        )

        assert len(suggestions) == 1
        clip = suggestions[0]
        assert isinstance(clip, ClipSuggestion)
        assert clip.start_time >= 0
        assert clip.end_time <= episode_data["duration"]
        assert clip.duration >= 15.0
        assert clip.duration <= 120.0
        assert clip.highlight_score == 0.8
        assert len(clip.title_variants) > 0
