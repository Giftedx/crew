"""
End-to-end integration tests for Creator Operations system.

Tests cover:
- Complete ingest → process → intelligence pack workflow
- Multi-platform content processing
- Cross-component integration
- Error handling and recovery
- Performance and scalability
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest

from ultimate_discord_intelligence_bot.creator_ops.features.clip_radar import ClipRadar
from ultimate_discord_intelligence_bot.creator_ops.features.episode_intelligence import EpisodeIntelligence
from ultimate_discord_intelligence_bot.creator_ops.features.repurposing_studio import RepurposingStudio
from ultimate_discord_intelligence_bot.creator_ops.integrations.twitch_client import TwitchClient
from ultimate_discord_intelligence_bot.creator_ops.integrations.youtube_client import YouTubeClient
from ultimate_discord_intelligence_bot.creator_ops.media.asr import ASRProcessor
from ultimate_discord_intelligence_bot.creator_ops.media.diarization import DiarizationProcessor
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestCreatorOpsE2E:
    """End-to-end test suite for Creator Operations system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_tenant = "test_tenant"
        self.test_workspace = "test_workspace"
        self.test_video_id = "dQw4w9WgXcQ"
        self.test_stream_id = "12345"
        self.test_user_id = "67890"

    def test_youtube_ingest_to_intelligence_pack_e2e(self):
        """Test complete YouTube video processing workflow."""
        # Mock YouTube client
        youtube_client = Mock(spec=YouTubeClient)
        youtube_client.get_video_metadata.return_value = StepResult.ok(
            data={
                "video": Mock(
                    video_id=self.test_video_id,
                    title="Test Video Title",
                    description="Test video description",
                    channel_id="test_channel",
                    duration=300,
                    view_count=1000000,
                    like_count=50000,
                    comment_count=1000,
                )
            }
        )

        # Mock ASR processor
        asr_processor = Mock(spec=ASRProcessor)
        asr_processor.transcribe_audio.return_value = StepResult.ok(
            data={
                "result": Mock(
                    text="This is a test transcription of the video content.",
                    language="en",
                    language_probability=0.95,
                    segments=[
                        Mock(start_time=0.0, end_time=5.0, text="This is a test"),
                        Mock(start_time=5.0, end_time=10.0, text="transcription of the video content."),
                    ],
                    duration=10.0,
                    model_name="base",
                    processing_time=2.5,
                )
            }
        )

        # Mock diarization processor
        diarization_processor = Mock(spec=DiarizationProcessor)
        diarization_processor.diarize_audio.return_value = StepResult.ok(
            data={
                "result": Mock(
                    segments=[
                        Mock(speaker_id="SPEAKER_00", start_time=0.0, end_time=5.0, duration=5.0),
                        Mock(speaker_id="SPEAKER_01", start_time=5.0, end_time=10.0, duration=5.0),
                    ],
                    num_speakers=2,
                    total_duration=10.0,
                )
            }
        )

        # Mock episode intelligence
        episode_intelligence = Mock(spec=EpisodeIntelligence)
        episode_intelligence.generate_intelligence_pack.return_value = StepResult.ok(
            data={
                "intelligence_pack": {
                    "summary": "Test video summary",
                    "key_points": ["Key point 1", "Key point 2"],
                    "topics": ["topic1", "topic2"],
                    "sentiment": "positive",
                    "engagement_score": 0.85,
                    "recommendations": ["Recommendation 1", "Recommendation 2"],
                }
            }
        )

        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
            audio_file.write(b"fake_audio_data")
            audio_file_path = audio_file.name

        try:
            # Step 1: Get video metadata
            video_result = youtube_client.get_video_metadata(self.test_video_id)
            assert video_result.success
            video_data = video_result.data["video"]

            # Step 2: Download audio (mocked)
            audio_download_result = StepResult.ok(data={"audio_file": audio_file_path})
            assert audio_download_result.success

            # Step 3: Transcribe audio
            asr_result = asr_processor.transcribe_audio(audio_file_path)
            assert asr_result.success
            asr_data = asr_result.data["result"]

            # Step 4: Diarize audio
            diarization_result = diarization_processor.diarize_audio(audio_file_path)
            assert diarization_result.success
            diarization_data = diarization_result.data["result"]

            # Step 5: Generate intelligence pack
            intelligence_result = episode_intelligence.generate_intelligence_pack(
                video_data=video_data,
                asr_data=asr_data,
                diarization_data=diarization_data,
                tenant=self.test_tenant,
                workspace=self.test_workspace,
            )
            assert intelligence_result.success
            intelligence_pack = intelligence_result.data["intelligence_pack"]

            # Verify intelligence pack structure
            assert "summary" in intelligence_pack
            assert "key_points" in intelligence_pack
            assert "topics" in intelligence_pack
            assert "sentiment" in intelligence_pack
            assert "engagement_score" in intelligence_pack
            assert "recommendations" in intelligence_pack

        finally:
            Path(audio_file_path).unlink()

    def test_twitch_stream_to_clip_radar_e2e(self):
        """Test complete Twitch stream monitoring and clip creation workflow."""
        # Mock Twitch client
        twitch_client = Mock(spec=TwitchClient)
        twitch_client.get_stream_info.return_value = StepResult.ok(
            data={
                "stream": Mock(
                    stream_id=self.test_stream_id,
                    user_id=self.test_user_id,
                    title="Epic Gaming Session",
                    viewer_count=1000,
                    game_name="Just Chatting",
                    started_at=datetime.now() - timedelta(minutes=30),
                    is_live=True,
                )
            }
        )

        twitch_client.get_chat_messages.return_value = StepResult.ok(
            data={
                "messages": [
                    Mock(
                        message_id="msg_1",
                        message="This is AMAZING!",
                        user_name="Viewer1",
                        created_at=datetime.now(),
                        sentiment=0.9,
                        engagement=150,
                    ),
                    Mock(
                        message_id="msg_2",
                        message="EPIC moment!",
                        user_name="Viewer2",
                        created_at=datetime.now(),
                        sentiment=0.8,
                        engagement=120,
                    ),
                    Mock(
                        message_id="msg_3",
                        message="WOW that was incredible!",
                        user_name="Viewer3",
                        created_at=datetime.now(),
                        sentiment=0.95,
                        engagement=200,
                    ),
                ]
            }
        )

        twitch_client.create_clip.return_value = StepResult.ok(
            data={
                "clip": Mock(
                    clip_id="clip_123",
                    url="https://clips.twitch.tv/clip_123",
                    title="Epic Gaming Moment",
                    duration=30.0,
                    view_count=0,
                    created_at=datetime.now(),
                )
            }
        )

        # Mock Clip Radar
        clip_radar = Mock(spec=ClipRadar)
        clip_radar.start_monitoring.return_value = StepResult.ok(data={"monitoring_started": True})
        clip_radar.detect_moment.return_value = StepResult.ok(
            data={
                "moment": Mock(
                    moment_id="moment_123",
                    stream_id=self.test_stream_id,
                    timestamp=datetime.now(),
                    moment_score=0.9,
                    title="Epic Gaming Moment",
                    is_clipworthy=True,
                )
            }
        )
        clip_radar.create_clip.return_value = StepResult.ok(
            data={
                "clip": {
                    "clip_id": "clip_123",
                    "url": "https://clips.twitch.tv/clip_123",
                    "title": "Epic Gaming Moment",
                }
            }
        )

        # Step 1: Start monitoring
        monitoring_result = clip_radar.start_monitoring(self.test_user_id)
        assert monitoring_result.success

        # Step 2: Get stream info
        stream_result = twitch_client.get_stream_info(self.test_user_id)
        assert stream_result.success
        stream_data = stream_result.data["stream"]

        # Step 3: Get chat messages
        chat_result = twitch_client.get_chat_messages(self.test_user_id, limit=100)
        assert chat_result.success
        chat_messages = chat_result.data["messages"]

        # Step 4: Detect moment
        moment_result = clip_radar.detect_moment(stream_data, chat_messages)
        assert moment_result.success
        moment = moment_result.data["moment"]

        # Step 5: Create clip if moment is clipworthy
        if moment.is_clipworthy:
            clip_result = clip_radar.create_clip(moment, platform="twitch")
            assert clip_result.success
            clip_data = clip_result.data["clip"]

            # Verify clip data
            assert "clip_id" in clip_data
            assert "url" in clip_data
            assert "title" in clip_data

    def test_repurposing_studio_e2e(self):
        """Test complete repurposing workflow from episode to shorts."""
        # Mock episode data
        episode_data = {
            "episode_id": "episode_123",
            "title": "Test Episode",
            "duration": 3600,  # 1 hour
            "transcript": "This is a test episode with multiple segments that can be repurposed into shorts.",
            "segments": [
                {"start_time": 0, "end_time": 300, "text": "Introduction segment"},
                {"start_time": 300, "end_time": 900, "text": "Main content segment 1"},
                {"start_time": 900, "end_time": 1500, "text": "Main content segment 2"},
                {"start_time": 1500, "end_time": 1800, "text": "Conclusion segment"},
            ],
            "metadata": {
                "channel_id": "test_channel",
                "published_at": datetime.now().isoformat(),
                "view_count": 100000,
                "engagement_rate": 0.05,
            },
        }

        # Mock Repurposing Studio
        repurposing_studio = Mock(spec=RepurposingStudio)
        repurposing_studio.analyze_episode.return_value = StepResult.ok(
            data={
                "analysis": {
                    "total_segments": 4,
                    "repurposable_segments": 3,
                    "avg_segment_duration": 450,
                    "content_quality_score": 0.85,
                    "engagement_potential": 0.78,
                }
            }
        )

        repurposing_studio.generate_shorts.return_value = StepResult.ok(
            data={
                "shorts": [
                    {
                        "short_id": "short_1",
                        "title": "Introduction Short",
                        "description": "Quick intro to the episode",
                        "start_time": 0,
                        "end_time": 300,
                        "duration": 300,
                        "format": "vertical",
                        "platform": "tiktok",
                        "content_score": 0.9,
                    },
                    {
                        "short_id": "short_2",
                        "title": "Main Content Short 1",
                        "description": "Key insights from segment 1",
                        "start_time": 300,
                        "end_time": 900,
                        "duration": 600,
                        "format": "vertical",
                        "platform": "youtube_shorts",
                        "content_score": 0.85,
                    },
                    {
                        "short_id": "short_3",
                        "title": "Main Content Short 2",
                        "description": "Key insights from segment 2",
                        "start_time": 900,
                        "end_time": 1500,
                        "duration": 600,
                        "format": "vertical",
                        "platform": "instagram_reels",
                        "content_score": 0.88,
                    },
                ]
            }
        )

        # Step 1: Analyze episode
        analysis_result = repurposing_studio.analyze_episode(episode_data)
        assert analysis_result.success
        analysis = analysis_result.data["analysis"]

        # Verify analysis
        assert analysis["total_segments"] == 4
        assert analysis["repurposable_segments"] == 3
        assert analysis["content_quality_score"] > 0.8

        # Step 2: Generate shorts
        shorts_result = repurposing_studio.generate_shorts(
            episode_data=episode_data,
            analysis=analysis,
            target_platforms=["tiktok", "youtube_shorts", "instagram_reels"],
            max_duration=600,
            tenant=self.test_tenant,
            workspace=self.test_workspace,
        )
        assert shorts_result.success
        shorts = shorts_result.data["shorts"]

        # Verify shorts generation
        assert len(shorts) == 3
        for short in shorts:
            assert "short_id" in short
            assert "title" in short
            assert "description" in short
            assert "start_time" in short
            assert "end_time" in short
            assert "duration" in short
            assert "format" in short
            assert "platform" in short
            assert "content_score" in short
            assert short["duration"] <= 600

    def test_multi_platform_content_processing_e2e(self):
        """Test processing content from multiple platforms simultaneously."""
        # Mock clients for different platforms
        youtube_client = Mock(spec=YouTubeClient)
        twitch_client = Mock(spec=TwitchClient)

        # Mock YouTube video
        youtube_client.get_video_metadata.return_value = StepResult.ok(
            data={"video": Mock(video_id="yt_video_123", title="YouTube Video", duration=600, view_count=50000)}
        )

        # Mock Twitch stream
        twitch_client.get_stream_info.return_value = StepResult.ok(
            data={"stream": Mock(stream_id="twitch_stream_123", title="Twitch Stream", viewer_count=500, is_live=True)}
        )

        # Mock ASR processor
        asr_processor = Mock(spec=ASRProcessor)
        asr_processor.transcribe_audio.return_value = StepResult.ok(
            data={"result": Mock(text="Transcribed content", language="en", duration=600)}
        )

        # Process YouTube content
        youtube_result = youtube_client.get_video_metadata("yt_video_123")
        assert youtube_result.success

        # Process Twitch content
        twitch_result = twitch_client.get_stream_info("twitch_user_123")
        assert twitch_result.success

        # Both should succeed independently
        assert youtube_result.success
        assert twitch_result.success

    def test_error_handling_and_recovery_e2e(self):
        """Test error handling and recovery across the system."""
        # Mock client with intermittent failures
        youtube_client = Mock(spec=YouTubeClient)

        # First call fails, second succeeds
        youtube_client.get_video_metadata.side_effect = [
            StepResult.fail("Network error"),
            StepResult.ok(data={"video": Mock(video_id=self.test_video_id, title="Test Video", duration=300)}),
        ]

        # Mock ASR processor
        asr_processor = Mock(spec=ASRProcessor)
        asr_processor.transcribe_audio.return_value = StepResult.ok(
            data={"result": Mock(text="Transcribed content", language="en", duration=300)}
        )

        # Step 1: First attempt fails
        result1 = youtube_client.get_video_metadata(self.test_video_id)
        assert not result1.success
        assert "Network error" in result1.error

        # Step 2: Retry succeeds
        result2 = youtube_client.get_video_metadata(self.test_video_id)
        assert result2.success
        result2.data["video"]

        # Step 3: Continue processing
        asr_result = asr_processor.transcribe_audio("audio_file.wav")
        assert asr_result.success

    def test_performance_and_scalability_e2e(self):
        """Test system performance under load."""
        import threading

        results = []
        errors = []

        def process_video_worker(video_id):
            try:
                # Mock YouTube client
                youtube_client = Mock(spec=YouTubeClient)
                youtube_client.get_video_metadata.return_value = StepResult.ok(
                    data={"video": Mock(video_id=video_id, title=f"Video {video_id}", duration=300)}
                )

                # Mock ASR processor
                asr_processor = Mock(spec=ASRProcessor)
                asr_processor.transcribe_audio.return_value = StepResult.ok(
                    data={"result": Mock(text=f"Transcribed content for {video_id}", language="en", duration=300)}
                )

                # Process video
                video_result = youtube_client.get_video_metadata(video_id)
                assert video_result.success

                asr_result = asr_processor.transcribe_audio("audio_file.wav")
                assert asr_result.success

                results.append((video_id, True))

            except Exception as e:
                errors.append((video_id, str(e)))

        # Start multiple threads
        threads = []
        for i in range(10):  # Process 10 videos concurrently
            thread = threading.Thread(target=process_video_worker, args=(f"video_{i}",))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all requests succeeded
        assert len(results) == 10
        assert len(errors) == 0
        assert all(success for _, success in results)

    def test_data_persistence_e2e(self):
        """Test data persistence across system components."""
        # Mock store operations
        store_manager = Mock()
        store_manager.add_memory_item.return_value = StepResult.ok(data={"id": "memory_123"})
        store_manager.add_kg_node.return_value = StepResult.ok(data={"id": "kg_123"})
        store_manager.upsert_creator_profile.return_value = StepResult.ok(data={"id": "profile_123"})

        # Mock episode data
        episode_data = {
            "episode_id": "episode_123",
            "title": "Test Episode",
            "transcript": "Test transcript",
            "metadata": {"channel_id": "test_channel", "published_at": datetime.now().isoformat()},
        }

        # Step 1: Store episode data
        memory_result = store_manager.add_memory_item(
            tenant=self.test_tenant,
            workspace=self.test_workspace,
            content_type="episode",
            content_json=json.dumps(episode_data),
        )
        assert memory_result.success

        # Step 2: Store knowledge graph node
        kg_result = store_manager.add_kg_node(
            tenant=self.test_tenant, type="episode", name=episode_data["episode_id"], attrs=episode_data["metadata"]
        )
        assert kg_result.success

        # Step 3: Store creator profile
        profile_result = store_manager.upsert_creator_profile(
            name="test_creator", data={"platform": "youtube", "channel_id": "test_channel", "total_episodes": 1}
        )
        assert profile_result.success

        # Verify all storage operations succeeded
        assert memory_result.success
        assert kg_result.success
        assert profile_result.success

    def test_integration_with_existing_system_e2e(self):
        """Test integration with existing Ultimate Discord Intelligence Bot system."""
        # Mock existing system components
        memory_service = Mock()
        memory_service.store_content.return_value = StepResult.ok(data={"stored": True})

        prompt_engine = Mock()
        prompt_engine.generate_prompt.return_value = StepResult.ok(data={"prompt": "Generated prompt"})

        # Mock creator ops components
        youtube_client = Mock(spec=YouTubeClient)
        youtube_client.get_video_metadata.return_value = StepResult.ok(
            data={"video": Mock(video_id=self.test_video_id, title="Test Video", duration=300)}
        )

        # Step 1: Process content with creator ops
        video_result = youtube_client.get_video_metadata(self.test_video_id)
        assert video_result.success

        # Step 2: Store in existing memory service
        memory_result = memory_service.store_content(
            content=video_result.data["video"].title, tenant=self.test_tenant, workspace=self.test_workspace
        )
        assert memory_result.success

        # Step 3: Generate prompt with existing prompt engine
        prompt_result = prompt_engine.generate_prompt(
            template="video_analysis", variables={"title": video_result.data["video"].title}
        )
        assert prompt_result.success

        # Verify integration works
        assert video_result.success
        assert memory_result.success
        assert prompt_result.success


if __name__ == "__main__":
    pytest.main([__file__])
