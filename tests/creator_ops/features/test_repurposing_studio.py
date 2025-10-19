"""
Tests for the Repurposing Studio feature.
Tests clip generation, platform optimization, and AI agent integration.
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.features.repurposing_agent import RepurposingAgent
from ultimate_discord_intelligence_bot.creator_ops.features.repurposing_models import (
    AspectRatio,
    CaptionStyle,
    ClipCandidate,
    FFmpegConfig,
    PlatformType,
    RepurposingConfig,
    RepurposingJob,
    RepurposingResult,
)
from ultimate_discord_intelligence_bot.creator_ops.features.repurposing_studio import RepurposingStudio
from ultimate_discord_intelligence_bot.creator_ops.knowledge.api import KnowledgeAPI
from ultimate_discord_intelligence_bot.creator_ops.media.alignment import AlignedSegment, AlignedTranscript


class TestRepurposingStudio:
    """Test cases for RepurposingStudio."""

    @pytest.fixture
    def config(self):
        return Mock(spec=CreatorOpsConfig)

    @pytest.fixture
    def knowledge_api(self):
        return Mock(spec=KnowledgeAPI)

    @pytest.fixture
    def repurposing_studio(self, config, knowledge_api):
        return RepurposingStudio(config, knowledge_api)

    @pytest.fixture
    def sample_transcript(self):
        """Create a sample aligned transcript for testing."""
        segments = [
            AlignedSegment(
                start_time=0.0,
                end_time=30.0,
                text="Welcome to today's episode! We have an amazing guest with us.",
                speakers=["Host"],
                topics=["introduction", "guest"],
                sentiment_score=0.8,
            ),
            AlignedSegment(
                start_time=30.0,
                end_time=60.0,
                text="This is going to be an incredible conversation about technology and innovation.",
                speakers=["Guest"],
                topics=["technology", "innovation"],
                sentiment_score=0.9,
            ),
            AlignedSegment(
                start_time=60.0,
                end_time=90.0,
                text="I'm so excited to share my insights with your audience today.",
                speakers=["Guest"],
                topics=["excitement", "insights"],
                sentiment_score=0.7,
            ),
        ]

        return AlignedTranscript(
            segments=segments, duration=90.0, metadata={"title": "Amazing Tech Talk", "episode_id": "test_episode_123"}
        )

    @pytest.fixture
    def sample_config(self):
        """Create a sample repurposing configuration."""
        return RepurposingConfig(
            min_clip_duration=15.0,
            max_clip_duration=60.0,
            target_clip_count=3,
            include_speaker_labels=True,
            auto_generate_hooks=True,
        )

    def test_identify_clip_candidates(self, repurposing_studio, sample_transcript, sample_config):
        """Test clip candidate identification."""
        result = repurposing_studio._identify_clip_candidates(sample_transcript, sample_config)

        assert result.success
        assert "candidates" in result.data

        candidates = result.data["candidates"]
        assert len(candidates) > 0

        # Check candidate structure
        for candidate in candidates:
            assert isinstance(candidate, ClipCandidate)
            assert candidate.start_time >= 0
            assert candidate.end_time > candidate.start_time
            assert candidate.duration > 0
            assert candidate.transcript_segment
            assert candidate.speakers
            assert candidate.engagement_score >= 0
            assert candidate.viral_potential >= 0
            assert candidate.reason

    def test_is_valid_clip_segment(self, repurposing_studio, sample_config):
        """Test clip segment validation."""
        # Valid segment
        valid_segment = AlignedSegment(
            start_time=0.0,
            end_time=30.0,
            text="This is a valid segment with enough content to be considered for a clip.",
            speakers=["Host"],
            topics=["test"],
            sentiment_score=0.5,
        )

        assert repurposing_studio._is_valid_clip_segment(valid_segment, sample_config)

        # Invalid segment (too short)
        short_segment = AlignedSegment(
            start_time=0.0, end_time=5.0, text="Too short", speakers=["Host"], topics=[], sentiment_score=0.5
        )

        assert not repurposing_studio._is_valid_clip_segment(short_segment, sample_config)

        # Invalid segment (too long)
        long_segment = AlignedSegment(
            start_time=0.0,
            end_time=120.0,
            text="This segment is way too long for a clip and should not be considered valid.",
            speakers=["Host"],
            topics=[],
            sentiment_score=0.5,
        )

        assert not repurposing_studio._is_valid_clip_segment(long_segment, sample_config)

    def test_calculate_engagement_score(self, repurposing_studio, sample_transcript):
        """Test engagement score calculation."""
        segment = AlignedSegment(
            start_time=0.0,
            end_time=30.0,
            text="This is amazing! How did you do it?",
            speakers=["Host", "Guest"],
            topics=["amazing", "innovation"],
            sentiment_score=0.8,
        )

        score = repurposing_studio._calculate_engagement_score(segment, sample_transcript)

        assert 0 <= score <= 1.0
        assert score > 0  # Should have some engagement

    def test_calculate_viral_potential(self, repurposing_studio, sample_transcript):
        """Test viral potential calculation."""
        segment = AlignedSegment(
            start_time=0.0,
            end_time=30.0,
            text="This is going viral! Share this with everyone!",
            speakers=["Host"],
            topics=["viral", "trending"],
            sentiment_score=0.9,
        )

        score = repurposing_studio._calculate_viral_potential(segment, sample_transcript)

        assert 0 <= score <= 1.0
        assert score > 0  # Should have some viral potential

    def test_generate_selection_reason(self, repurposing_studio):
        """Test selection reason generation."""
        segment = AlignedSegment(
            start_time=0.0,
            end_time=30.0,
            text="This is amazing! How did you do it?",
            speakers=["Host", "Guest"],
            topics=["amazing", "innovation"],
            sentiment_score=0.8,
        )

        reason = repurposing_studio._generate_selection_reason(segment, 0.8, 0.7)

        assert reason
        assert "amazing" in reason.lower() or "engagement" in reason.lower()

    @patch("asyncio.create_subprocess_exec")
    async def test_process_video_with_ffmpeg(self, mock_subprocess, repurposing_studio, sample_config):
        """Test FFmpeg video processing."""
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        ffmpeg_config = FFmpegConfig(
            input_file="test_input.mp4",
            output_file="test_output.mp4",
            start_time=0.0,
            end_time=30.0,
            aspect_ratio=AspectRatio.VERTICAL_9_16,
            resolution="1080x1920",
        )

        result = await repurposing_studio._process_video_with_ffmpeg(ffmpeg_config, sample_config)

        assert result.success
        assert "output_file" in result.data

    async def test_generate_captions(self, repurposing_studio, sample_config):
        """Test caption generation."""
        candidate = ClipCandidate(
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            transcript_segment="This is a test segment for captions.",
            speakers=["Host"],
            topics=["test"],
            sentiment_score=0.5,
            engagement_score=0.7,
            viral_potential=0.6,
            reason="Test reason",
        )

        clip_dir = Path("/tmp/test_clip")
        clip_dir.mkdir(exist_ok=True)

        caption_style = CaptionStyle()

        result = await repurposing_studio._generate_captions(candidate, clip_dir, "test_clip", caption_style)

        assert result.success
        assert "captions_path" in result.data

        # Cleanup
        import shutil

        shutil.rmtree(clip_dir, ignore_errors=True)

    def test_generate_hook_text(self, repurposing_studio, sample_transcript):
        """Test platform-specific hook text generation."""
        platforms = [PlatformType.YOUTUBE_SHORTS, PlatformType.TIKTOK, PlatformType.INSTAGRAM_REELS, PlatformType.X]

        for platform in platforms:
            hook_text = repurposing_studio._generate_hook_text(platform, sample_transcript)
            assert hook_text
            assert len(hook_text) > 0

    def test_generate_hashtags(self, repurposing_studio, sample_transcript):
        """Test platform-specific hashtag generation."""
        platforms = [PlatformType.YOUTUBE_SHORTS, PlatformType.TIKTOK, PlatformType.INSTAGRAM_REELS, PlatformType.X]

        for platform in platforms:
            hashtags = repurposing_studio._generate_hashtags(platform, sample_transcript)
            assert isinstance(hashtags, list)
            assert len(hashtags) > 0
            assert all(hashtag.startswith("#") for hashtag in hashtags)

    def test_generate_call_to_action(self, repurposing_studio):
        """Test call-to-action generation."""
        platforms = [PlatformType.YOUTUBE_SHORTS, PlatformType.TIKTOK, PlatformType.INSTAGRAM_REELS, PlatformType.X]

        for platform in platforms:
            cta = repurposing_studio._generate_call_to_action(platform)
            assert cta
            assert len(cta) > 0

    def test_get_engagement_tips(self, repurposing_studio):
        """Test engagement tips generation."""
        platforms = [PlatformType.YOUTUBE_SHORTS, PlatformType.TIKTOK, PlatformType.INSTAGRAM_REELS, PlatformType.X]

        for platform in platforms:
            tips = repurposing_studio._get_engagement_tips(platform)
            assert isinstance(tips, list)
            assert len(tips) > 0

    @patch("asyncio.create_subprocess_exec")
    async def test_repurpose_episode(self, mock_subprocess, repurposing_studio, sample_transcript, sample_config):
        """Test complete episode repurposing workflow."""
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        target_platforms = [PlatformType.YOUTUBE_SHORTS, PlatformType.TIKTOK]
        video_file_path = "test_episode.mp4"

        result = await repurposing_studio.repurpose_episode(
            "test_episode_123", video_file_path, sample_transcript, target_platforms, sample_config
        )

        assert result.success
        assert "job" in result.data
        assert "result" in result.data

        job = result.data["job"]
        assert isinstance(job, RepurposingJob)
        assert job.episode_id == "test_episode_123"
        assert job.target_platforms == target_platforms

        repurposing_result = result.data["result"]
        assert isinstance(repurposing_result, RepurposingResult)
        assert repurposing_result.job_id == job.job_id
        assert repurposing_result.success
        assert repurposing_result.clips_created >= 0

    async def test_cleanup(self, repurposing_studio):
        """Test cleanup functionality."""
        # Create a temporary directory
        temp_dir = repurposing_studio.temp_dir
        temp_dir.mkdir(exist_ok=True)

        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        # Run cleanup
        await repurposing_studio.cleanup()

        # Directory should be cleaned up
        assert not temp_dir.exists()


class TestRepurposingAgent:
    """Test cases for RepurposingAgent."""

    @pytest.fixture
    def repurposing_studio(self):
        return Mock(spec=RepurposingStudio)

    @pytest.fixture
    def repurposing_agent(self, repurposing_studio):
        return RepurposingAgent(repurposing_studio)

    def test_create_agent(self, repurposing_agent):
        """Test agent creation."""
        assert repurposing_agent.agent is not None
        assert repurposing_agent.agent.role == "Content Repurposing Specialist"

    @patch("crewai.Agent.execute_task")
    async def test_analyze_content_for_repurposing(self, mock_execute_task, repurposing_agent):
        """Test content analysis."""
        mock_execute_task.return_value = """
        Key themes and topics:
        - Technology and innovation
        - Guest insights
        - Exciting conversation

        Most engaging segments:
        1. Introduction (0-30s) - High energy
        2. Guest insights (30-60s) - Valuable content
        3. Excitement (60-90s) - Emotional connection

        Platform-specific optimization:
        - YouTube Shorts: Keep under 60s, use trending audio
        - TikTok: Use #fyp hashtag, post during peak hours

        Viral potential: 8/10

        Content strategy suggestions:
        - Post during peak hours
        - Use trending hashtags
        - Engage with comments
        """

        result = await repurposing_agent.analyze_content_for_repurposing(
            "Test Episode",
            "This is a test transcript about technology and innovation.",
            [PlatformType.YOUTUBE_SHORTS, PlatformType.TIKTOK],
        )

        assert result.success
        assert "analysis" in result.data
        assert "recommendations" in result.data
        assert "viral_potential" in result.data
        assert "platform_optimizations" in result.data

    def test_parse_analysis_result(self, repurposing_agent):
        """Test analysis result parsing."""
        result_text = """
        Key themes and topics:
        - Technology
        - Innovation
        - Guest insights

        Most engaging segments:
        1. Introduction (0-30s)
        2. Guest insights (30-60s)

        Platform-specific optimization:
        - YouTube Shorts: Keep under 60s
        - TikTok: Use trending hashtags

        Viral potential: 8/10

        Content strategy suggestions:
        - Post during peak hours
        - Use trending hashtags
        """

        analysis = repurposing_agent._parse_analysis_result(result_text)

        assert "themes" in analysis
        assert "engaging_segments" in analysis
        assert "platform_optimizations" in analysis
        assert "viral_potential" in analysis
        assert "strategy_suggestions" in analysis

    def test_generate_recommendations(self, repurposing_agent):
        """Test recommendation generation."""
        analysis = {"themes": ["technology", "innovation"], "viral_potential": 8}

        target_platforms = [PlatformType.YOUTUBE_SHORTS, PlatformType.TIKTOK]

        recommendations = repurposing_agent._generate_recommendations(analysis, target_platforms)

        assert isinstance(recommendations, dict)
        assert "youtube_shorts" in recommendations
        assert "tiktok" in recommendations

        for platform_recs in recommendations.values():
            assert isinstance(platform_recs, list)
            assert len(platform_recs) > 0

    def test_format_candidates_for_agent(self, repurposing_agent):
        """Test candidate formatting for agent."""
        candidates = [
            ClipCandidate(
                start_time=0.0,
                end_time=30.0,
                duration=30.0,
                transcript_segment="Test segment 1",
                speakers=["Host"],
                topics=["test"],
                sentiment_score=0.5,
                engagement_score=0.7,
                viral_potential=0.6,
                reason="Test reason 1",
            ),
            ClipCandidate(
                start_time=30.0,
                end_time=60.0,
                duration=30.0,
                transcript_segment="Test segment 2",
                speakers=["Guest"],
                topics=["innovation"],
                sentiment_score=0.8,
                engagement_score=0.8,
                viral_potential=0.7,
                reason="Test reason 2",
            ),
        ]

        formatted = repurposing_agent._format_candidates_for_agent(candidates)

        assert "Candidate 1" in formatted
        assert "Candidate 2" in formatted
        assert "Test segment 1" in formatted
        assert "Test segment 2" in formatted

    def test_parse_clip_selection(self, repurposing_agent):
        """Test clip selection parsing."""
        candidates = [
            ClipCandidate(
                start_time=0.0,
                end_time=30.0,
                duration=30.0,
                transcript_segment="Test segment 1",
                speakers=["Host"],
                topics=["test"],
                sentiment_score=0.5,
                engagement_score=0.7,
                viral_potential=0.6,
                reason="Test reason 1",
            ),
            ClipCandidate(
                start_time=30.0,
                end_time=60.0,
                duration=30.0,
                transcript_segment="Test segment 2",
                speakers=["Guest"],
                topics=["innovation"],
                sentiment_score=0.8,
                engagement_score=0.8,
                viral_potential=0.7,
                reason="Test reason 2",
            ),
        ]

        result_text = "Selected clips: 1, 2"
        selected = repurposing_agent._parse_clip_selection(result_text, candidates, 2)

        assert len(selected) <= 2
        assert all(isinstance(candidate, ClipCandidate) for candidate in selected)

    def test_extract_optimization_notes(self, repurposing_agent):
        """Test optimization notes extraction."""
        result_text = """
        YouTube Shorts: Keep under 60 seconds, use trending audio
        TikTok: Use trending hashtags, post during peak hours
        Instagram Reels: Use trending audio, cross-post to Stories
        """

        notes = repurposing_agent._extract_optimization_notes(result_text)

        assert isinstance(notes, dict)
        assert len(notes) > 0

    @patch("crewai.Agent.execute_task")
    async def test_generate_content_strategy(self, mock_execute_task, repurposing_agent):
        """Test content strategy generation."""
        mock_execute_task.return_value = """
        Posting schedule recommendations:
        - YouTube Shorts: Post at 6 PM
        - TikTok: Post at 7 PM

        Cross-platform promotion strategy:
        - Share on Stories
        - Cross-post to other platforms

        Engagement tactics:
        - Respond to comments quickly
        - Use trending hashtags

        Performance tracking suggestions:
        - Track views and engagement
        - Monitor hashtag performance

        Content calendar ideas:
        - Plan weekly content themes
        - Schedule posts in advance
        """

        result = await repurposing_agent.generate_content_strategy(
            "Test Episode", [PlatformType.YOUTUBE_SHORTS, PlatformType.TIKTOK], 3
        )

        assert result.success
        assert "strategy" in result.data
        assert "posting_schedule" in result.data
        assert "promotion_tactics" in result.data
        assert "engagement_strategies" in result.data
        assert "performance_metrics" in result.data
        assert "content_calendar" in result.data

    def test_parse_strategy_result(self, repurposing_agent):
        """Test strategy result parsing."""
        result_text = """
        Posting schedule recommendations:
        - YouTube Shorts: Post at 6 PM
        - TikTok: Post at 7 PM

        Cross-platform promotion strategy:
        - Share on Stories
        - Cross-post to other platforms

        Engagement tactics:
        - Respond to comments quickly
        - Use trending hashtags

        Performance tracking suggestions:
        - Track views and engagement
        - Monitor hashtag performance

        Content calendar ideas:
        - Plan weekly content themes
        - Schedule posts in advance
        """

        strategy = repurposing_agent._parse_strategy_result(result_text)

        assert "posting_schedule" in strategy
        assert "promotion_tactics" in strategy
        assert "engagement_strategies" in strategy
        assert "performance_metrics" in strategy
        assert "content_calendar" in strategy
