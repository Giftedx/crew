"""End-to-end tests for the complete Discord workflow."""

import asyncio
from platform.core.step_result import StepResult
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ultimate_discord_intelligence_bot.autonomous_orchestrator import AutonomousOrchestrator
from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext


class TestCompleteDiscordWorkflow:
    """End-to-end tests for the complete Discord workflow."""

    @pytest.fixture
    def autonomous_orchestrator(self):
        """Create an AutonomousOrchestrator instance."""
        return AutonomousOrchestrator()

    @pytest.fixture
    def content_pipeline(self):
        """Create a ContentPipeline instance."""
        return ContentPipeline()

    @pytest.fixture
    def test_tenant_context(self):
        """Create a test tenant context."""
        return TenantContext(tenant="test_tenant", workspace="test_workspace")

    @pytest.fixture
    def mock_discord_interaction(self):
        """Create a comprehensive mock Discord interaction."""
        interaction = MagicMock()
        interaction.guild = MagicMock()
        interaction.guild.id = "test_guild_123"
        interaction.guild.name = "Test Guild"
        interaction.channel = MagicMock()
        interaction.channel.id = "test_channel_123"
        interaction.channel.name = "test-channel"
        interaction.user = MagicMock()
        interaction.user.id = "test_user_123"
        interaction.user.name = "test_user"
        interaction.user.display_name = "Test User"
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()
        interaction.edit_original_response = AsyncMock()
        return interaction

    @pytest.mark.asyncio
    async def test_complete_youtube_analysis_workflow(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete YouTube analysis workflow from Discord to final output."""
        url = "https://youtube.com/watch?v=test123"
        depth = "comprehensive"
        with patch.object(content_pipeline, "_download_youtube_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={
                    "url": url,
                    "title": "AI and the Future of Work: A Comprehensive Debate",
                    "duration": 1800,
                    "quality": "1080p",
                    "views": 50000,
                    "likes": 2500,
                    "dislikes": 100,
                    "channel": "TechDebates",
                    "published": "2024-01-15T10:00:00Z",
                }
            )
            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={
                        "transcript": "Welcome to TechDebates. Today we're discussing AI and the future of work. This is a complex topic that affects millions of workers worldwide. Let's start with the arguments for AI automation...",
                        "language": "en",
                        "confidence": 0.95,
                        "word_count": 4500,
                        "speaker_segments": [
                            {"speaker": "host", "start": 0, "end": 30, "text": "Welcome to TechDebates..."},
                            {"speaker": "guest1", "start": 30, "end": 120, "text": "AI will revolutionize work..."},
                        ],
                    }
                )
                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={
                            "sentiment": "neutral",
                            "topics": ["AI", "automation", "employment", "technology", "future"],
                            "debate_score": 0.85,
                            "fact_check_score": 0.78,
                            "bias_score": 0.25,
                            "credibility_score": 0.82,
                            "argument_quality": 0.88,
                            "evidence_quality": 0.75,
                            "speaker_analysis": {
                                "host": {"bias": 0.15, "credibility": 0.9},
                                "guest1": {"bias": 0.3, "credibility": 0.85},
                            },
                        }
                    )
                    with patch.object(content_pipeline, "_calculate_spam_score") as mock_spam:
                        mock_spam.return_value = 0.05
                        with patch.object(content_pipeline, "_calculate_wer") as mock_wer:
                            mock_wer.return_value = 0.03
                            with patch.object(content_pipeline, "_calculate_repetition_ratio") as mock_repetition:
                                mock_repetition.return_value = 0.12
                                with patch.object(
                                    content_pipeline, "_calculate_vocabulary_diversity"
                                ) as mock_diversity:
                                    mock_diversity.return_value = 0.88
                                    with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
                                        mock_memory.return_value = StepResult.ok(
                                            data={
                                                "memory_id": "mem_123",
                                                "stored": True,
                                                "vector_count": 150,
                                                "embeddings_created": 150,
                                            }
                                        )
                                        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
                                            mock_discord.return_value = StepResult.ok(
                                                data={
                                                    "message_id": "msg_123",
                                                    "sent": True,
                                                    "channel_id": "test_channel_123",
                                                }
                                            )
                                            result = (
                                                await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                                    interaction=mock_discord_interaction, url=url, depth=depth
                                                )
                                            )
        assert result is not None
        mock_discord_interaction.response.send_message.assert_called_once()
        mock_discord_interaction.followup.send.assert_called()
        mock_download.assert_called_once()
        mock_transcribe.assert_called_once()
        mock_analyze.assert_called_once()
        mock_spam.assert_called_once()
        mock_wer.assert_called_once()
        mock_repetition.assert_called_once()
        mock_diversity.assert_called_once()
        mock_memory.assert_called_once()
        mock_discord.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_twitch_stream_analysis_workflow(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete Twitch stream analysis workflow."""
        url = "https://twitch.tv/videos/test123"
        depth = "comprehensive"
        with patch.object(content_pipeline, "_download_twitch_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={
                    "url": url,
                    "title": "Live Debate: Climate Change Solutions",
                    "duration": 7200,
                    "viewer_count": 15000,
                    "category": "Just Chatting",
                    "streamer": "EcoDebater",
                    "started_at": "2024-01-15T14:00:00Z",
                }
            )
            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={
                        "transcript": "Welcome to today's live debate on climate change solutions. We have experts from both sides here to discuss the most effective approaches to addressing climate change...",
                        "language": "en",
                        "confidence": 0.92,
                        "word_count": 8000,
                        "speaker_segments": [
                            {"speaker": "host", "start": 0, "end": 60, "text": "Welcome to today's live debate..."},
                            {"speaker": "expert1", "start": 60, "end": 300, "text": "Renewable energy is the key..."},
                        ],
                    }
                )
                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={
                            "sentiment": "mixed",
                            "topics": ["climate_change", "renewable_energy", "policy", "environment"],
                            "debate_score": 0.92,
                            "fact_check_score": 0.85,
                            "bias_score": 0.35,
                            "credibility_score": 0.88,
                            "argument_quality": 0.9,
                            "evidence_quality": 0.82,
                            "live_engagement": {"chat_activity": 0.75, "viewer_retention": 0.68},
                        }
                    )
                    with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
                        mock_memory.return_value = StepResult.ok(
                            data={
                                "memory_id": "mem_456",
                                "stored": True,
                                "vector_count": 200,
                                "embeddings_created": 200,
                            }
                        )
                        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
                            mock_discord.return_value = StepResult.ok(
                                data={"message_id": "msg_456", "sent": True, "channel_id": "test_channel_123"}
                            )
                            result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                interaction=mock_discord_interaction, url=url, depth=depth
                            )
        assert result is not None
        mock_download.assert_called_once()
        mock_transcribe.assert_called_once()
        mock_analyze.assert_called_once()
        mock_memory.assert_called_once()
        mock_discord.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_tiktok_video_analysis_workflow(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete TikTok video analysis workflow."""
        url = "https://tiktok.com/@user/video/test123"
        depth = "comprehensive"
        with patch.object(content_pipeline, "_download_tiktok_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={
                    "url": url,
                    "title": "Quick Take: AI Ethics Debate",
                    "duration": 60,
                    "hashtags": ["#AI", "#ethics", "#debate", "#tech"],
                    "likes": 5000,
                    "shares": 200,
                    "comments": 150,
                    "creator": "@TechEthicist",
                }
            )
            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={
                        "transcript": "AI ethics is a crucial topic. Should we prioritize safety over innovation? Let's break this down quickly...",
                        "language": "en",
                        "confidence": 0.88,
                        "word_count": 200,
                        "speaker_segments": [
                            {"speaker": "creator", "start": 0, "end": 60, "text": "AI ethics is a crucial topic..."}
                        ],
                    }
                )
                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={
                            "sentiment": "positive",
                            "topics": ["AI", "ethics", "technology", "innovation"],
                            "debate_score": 0.65,
                            "fact_check_score": 0.7,
                            "bias_score": 0.2,
                            "credibility_score": 0.75,
                            "argument_quality": 0.8,
                            "evidence_quality": 0.65,
                            "short_form_analysis": {"engagement_potential": 0.85, "viral_potential": 0.7},
                        }
                    )
                    with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
                        mock_memory.return_value = StepResult.ok(
                            data={"memory_id": "mem_789", "stored": True, "vector_count": 50, "embeddings_created": 50}
                        )
                        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
                            mock_discord.return_value = StepResult.ok(
                                data={"message_id": "msg_789", "sent": True, "channel_id": "test_channel_123"}
                            )
                            result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                interaction=mock_discord_interaction, url=url, depth=depth
                            )
        assert result is not None
        mock_download.assert_called_once()
        mock_transcribe.assert_called_once()
        mock_analyze.assert_called_once()
        mock_memory.assert_called_once()
        mock_discord.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_reddit_discussion_analysis_workflow(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete Reddit discussion analysis workflow."""
        url = "https://reddit.com/r/politics/comments/test123"
        depth = "comprehensive"
        with patch.object(content_pipeline, "_download_reddit_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={
                    "url": url,
                    "title": "CMV: Universal Basic Income is the solution to automation",
                    "subreddit": "politics",
                    "upvotes": 2500,
                    "downvotes": 800,
                    "comments": 500,
                    "text": "I believe UBI is the best solution to address job displacement from automation. Here's my reasoning...",
                    "author": "EconomicThinker",
                    "created_utc": "2024-01-15T08:00:00Z",
                }
            )
            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={
                        "transcript": "I believe UBI is the best solution to address job displacement from automation. Here's my reasoning based on economic theory and real-world examples...",
                        "language": "en",
                        "confidence": 0.94,
                        "word_count": 1200,
                        "speaker_segments": [
                            {
                                "speaker": "author",
                                "start": 0,
                                "end": 120,
                                "text": "I believe UBI is the best solution...",
                            }
                        ],
                    }
                )
                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={
                            "sentiment": "positive",
                            "topics": ["UBI", "automation", "economics", "policy", "employment"],
                            "debate_score": 0.88,
                            "fact_check_score": 0.82,
                            "bias_score": 0.4,
                            "credibility_score": 0.85,
                            "argument_quality": 0.92,
                            "evidence_quality": 0.88,
                            "discussion_analysis": {"controversy_level": 0.75, "engagement_quality": 0.8},
                        }
                    )
                    with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
                        mock_memory.return_value = StepResult.ok(
                            data={
                                "memory_id": "mem_101",
                                "stored": True,
                                "vector_count": 100,
                                "embeddings_created": 100,
                            }
                        )
                        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
                            mock_discord.return_value = StepResult.ok(
                                data={"message_id": "msg_101", "sent": True, "channel_id": "test_channel_123"}
                            )
                            result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                interaction=mock_discord_interaction, url=url, depth=depth
                            )
        assert result is not None
        mock_download.assert_called_once()
        mock_transcribe.assert_called_once()
        mock_analyze.assert_called_once()
        mock_memory.assert_called_once()
        mock_discord.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_workflow_with_error_recovery(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete workflow with error recovery mechanisms."""
        url = "https://youtube.com/watch?v=test123"
        depth = "comprehensive"
        call_count = 0

        async def mock_download_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return StepResult.fail("Network timeout")
            elif call_count == 2:
                return StepResult.fail("Rate limited")
            else:
                return StepResult.ok(data={"url": url, "title": "Test Video", "duration": 600})

        with patch.object(content_pipeline, "_download_youtube_content", side_effect=mock_download_with_retry):
            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={"transcript": "This is a test transcript", "language": "en", "confidence": 0.95}
                )
                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={"sentiment": "positive", "topics": ["technology"], "debate_score": 0.7}
                    )
                    with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
                        mock_memory.return_value = StepResult.ok(data={"memory_id": "mem_123", "stored": True})
                        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
                            mock_discord.return_value = StepResult.ok(data={"message_id": "msg_123", "sent": True})
                            result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                interaction=mock_discord_interaction, url=url, depth=depth
                            )
        assert result is not None
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_complete_workflow_with_quality_assessment(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete workflow with comprehensive quality assessment."""
        url = "https://youtube.com/watch?v=test123"
        depth = "comprehensive"
        with patch.object(content_pipeline, "_calculate_spam_score") as mock_spam:
            mock_spam.return_value = 0.05
            with patch.object(content_pipeline, "_calculate_wer") as mock_wer:
                mock_wer.return_value = 0.02
                with patch.object(content_pipeline, "_calculate_repetition_ratio") as mock_repetition:
                    mock_repetition.return_value = 0.08
                    with patch.object(content_pipeline, "_calculate_vocabulary_diversity") as mock_diversity:
                        mock_diversity.return_value = 0.92
                        with patch.object(content_pipeline, "_download_youtube_content") as mock_download:
                            mock_download.return_value = StepResult.ok(
                                data={"url": url, "title": "High-Quality Debate: The Future of AI", "duration": 1200}
                            )
                            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                                mock_transcribe.return_value = StepResult.ok(
                                    data={
                                        "transcript": "This is a high-quality transcript with diverse vocabulary and clear structure",
                                        "language": "en",
                                        "confidence": 0.98,
                                    }
                                )
                                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                                    mock_analyze.return_value = StepResult.ok(
                                        data={
                                            "sentiment": "neutral",
                                            "topics": ["AI", "technology", "future"],
                                            "debate_score": 0.85,
                                            "fact_check_score": 0.9,
                                            "bias_score": 0.15,
                                            "credibility_score": 0.95,
                                        }
                                    )
                                    with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
                                        mock_memory.return_value = StepResult.ok(
                                            data={"memory_id": "mem_123", "stored": True}
                                        )
                                        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
                                            mock_discord.return_value = StepResult.ok(
                                                data={"message_id": "msg_123", "sent": True}
                                            )
                                            result = (
                                                await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                                    interaction=mock_discord_interaction, url=url, depth=depth
                                                )
                                            )
        assert result is not None
        mock_spam.assert_called_once()
        mock_wer.assert_called_once()
        mock_repetition.assert_called_once()
        mock_diversity.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_workflow_with_performance_monitoring(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete workflow with performance monitoring."""
        url = "https://youtube.com/watch?v=test123"
        depth = "comprehensive"
        with patch.object(autonomous_orchestrator, "_record_performance_metrics") as mock_metrics:
            with patch.object(content_pipeline, "_download_youtube_content") as mock_download:
                mock_download.return_value = StepResult.ok(data={"url": url, "title": "Test Video", "duration": 600})
                with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                    mock_transcribe.return_value = StepResult.ok(
                        data={"transcript": "This is a test transcript", "language": "en", "confidence": 0.95}
                    )
                    with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                        mock_analyze.return_value = StepResult.ok(
                            data={"sentiment": "positive", "topics": ["technology"], "debate_score": 0.7}
                        )
                        with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
                            mock_memory.return_value = StepResult.ok(data={"memory_id": "mem_123", "stored": True})
                            with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
                                mock_discord.return_value = StepResult.ok(data={"message_id": "msg_123", "sent": True})
                                result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                    interaction=mock_discord_interaction, url=url, depth=depth
                                )
        assert result is not None
        mock_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_workflow_with_tenant_isolation(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction
    ):
        """Test complete workflow with tenant isolation."""
        url = "https://youtube.com/watch?v=test123"
        depth = "comprehensive"
        tenants = [("tenant1", "workspace1"), ("tenant2", "workspace2"), ("tenant3", "workspace3")]
        results = {}
        for tenant, workspace in tenants:
            with patch.object(content_pipeline, "_download_youtube_content") as mock_download:
                mock_download.return_value = StepResult.ok(
                    data={"url": url, "title": "Test Video", "tenant": tenant, "workspace": workspace}
                )
                with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                    mock_transcribe.return_value = StepResult.ok(
                        data={"transcript": "This is a test transcript", "language": "en", "confidence": 0.95}
                    )
                    with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                        mock_analyze.return_value = StepResult.ok(
                            data={"sentiment": "positive", "topics": ["technology"], "debate_score": 0.7}
                        )
                        with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
                            mock_memory.return_value = StepResult.ok(
                                data={"memory_id": f"mem_{tenant}", "stored": True}
                            )
                            with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
                                mock_discord.return_value = StepResult.ok(
                                    data={"message_id": f"msg_{tenant}", "sent": True}
                                )
                                result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                    interaction=mock_discord_interaction, url=url, depth=depth
                                )
                                results[f"{tenant}_{workspace}"] = result
        for key, result in results.items():
            assert result is not None, f"Failed for tenant {key}"

    @pytest.mark.asyncio
    async def test_complete_workflow_with_concurrent_execution(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction
    ):
        """Test complete workflow with concurrent execution."""
        urls = [
            "https://youtube.com/watch?v=test1",
            "https://youtube.com/watch?v=test2",
            "https://youtube.com/watch?v=test3",
        ]
        with patch.object(content_pipeline, "_download_youtube_content") as mock_download:
            mock_download.return_value = StepResult.ok(data={"url": "test", "title": "Test Video", "duration": 600})
            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={"transcript": "This is a test transcript", "language": "en", "confidence": 0.95}
                )
                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={"sentiment": "positive", "topics": ["technology"], "debate_score": 0.7}
                    )
                    with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
                        mock_memory.return_value = StepResult.ok(data={"memory_id": "mem_123", "stored": True})
                        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
                            mock_discord.return_value = StepResult.ok(data={"message_id": "msg_123", "sent": True})
                            tasks = [
                                autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                    interaction=mock_discord_interaction, url=url, depth="comprehensive"
                                )
                                for url in urls
                            ]
                            results = await asyncio.gather(*tasks)
        for result in results:
            assert result is not None

    @pytest.mark.asyncio
    async def test_complete_workflow_with_memory_integration(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete workflow with memory integration."""
        url = "https://youtube.com/watch?v=test123"
        depth = "comprehensive"
        with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
            mock_memory.return_value = StepResult.ok(
                data={"memory_id": "mem_123", "stored": True, "vector_count": 100, "embeddings_created": 100}
            )
            with patch.object(content_pipeline, "_download_youtube_content") as mock_download:
                mock_download.return_value = StepResult.ok(data={"url": url, "title": "Test Video", "duration": 600})
                with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                    mock_transcribe.return_value = StepResult.ok(
                        data={"transcript": "This is a test transcript", "language": "en", "confidence": 0.95}
                    )
                    with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                        mock_analyze.return_value = StepResult.ok(
                            data={"sentiment": "positive", "topics": ["technology"], "debate_score": 0.7}
                        )
                        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
                            mock_discord.return_value = StepResult.ok(data={"message_id": "msg_123", "sent": True})
                            result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                interaction=mock_discord_interaction, url=url, depth=depth
                            )
        assert result is not None
        mock_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_workflow_with_discord_integration(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete workflow with Discord integration."""
        url = "https://youtube.com/watch?v=test123"
        depth = "comprehensive"
        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
            mock_discord.return_value = StepResult.ok(
                data={"message_id": "msg_123", "sent": True, "channel_id": "test_channel_123"}
            )
            with patch.object(content_pipeline, "_download_youtube_content") as mock_download:
                mock_download.return_value = StepResult.ok(data={"url": url, "title": "Test Video", "duration": 600})
                with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                    mock_transcribe.return_value = StepResult.ok(
                        data={"transcript": "This is a test transcript", "language": "en", "confidence": 0.95}
                    )
                    with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                        mock_analyze.return_value = StepResult.ok(
                            data={"sentiment": "positive", "topics": ["technology"], "debate_score": 0.7}
                        )
                        with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
                            mock_memory.return_value = StepResult.ok(data={"memory_id": "mem_123", "stored": True})
                            result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                interaction=mock_discord_interaction, url=url, depth=depth
                            )
        assert result is not None
        mock_discord.assert_called_once()
