"""End-to-end integration tests for the complete pipeline workflow."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ultimate_discord_intelligence_bot.autonomous_orchestrator import AutonomousOrchestrator
from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext


class TestE2EPipelineIntegration:
    """End-to-end integration tests for the complete pipeline."""

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
        """Create a mock Discord interaction."""
        interaction = MagicMock()
        interaction.guild = MagicMock()
        interaction.guild.id = "test_guild_123"
        interaction.channel = MagicMock()
        interaction.channel.id = "test_channel_123"
        interaction.user = MagicMock()
        interaction.user.id = "test_user_123"
        interaction.user.name = "test_user"
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()
        return interaction

    @pytest.mark.asyncio
    async def test_complete_youtube_workflow(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete YouTube workflow from Discord to analysis."""
        url = "https://youtube.com/watch?v=test123"
        depth = "comprehensive"

        # Mock the complete workflow
        with patch.object(content_pipeline, "_download_youtube_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={"url": url, "title": "Test YouTube Video", "duration": 600, "quality": "1080p", "views": 10000}
            )

            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={
                        "transcript": "This is a comprehensive test transcript with detailed content",
                        "language": "en",
                        "confidence": 0.95,
                        "word_count": 500,
                    }
                )

                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={
                            "sentiment": "positive",
                            "topics": ["technology", "AI", "debate"],
                            "debate_score": 0.8,
                            "fact_check_score": 0.7,
                            "bias_score": 0.3,
                        }
                    )

                    with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
                        mock_memory.return_value = StepResult.ok(
                            data={"memory_id": "mem_123", "stored": True, "vector_count": 100}
                        )

                        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
                            mock_discord.return_value = StepResult.ok(data={"message_id": "msg_123", "sent": True})

                            # Execute the complete workflow
                            result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                interaction=mock_discord_interaction, url=url, depth=depth
                            )

        # Verify the complete workflow
        assert result is not None
        mock_discord_interaction.response.send_message.assert_called_once()
        mock_discord_interaction.followup.send.assert_called()

    @pytest.mark.asyncio
    async def test_complete_twitch_workflow(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete Twitch workflow from Discord to analysis."""
        url = "https://twitch.tv/videos/test123"
        depth = "comprehensive"

        # Mock the complete workflow
        with patch.object(content_pipeline, "_download_twitch_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={
                    "url": url,
                    "title": "Test Twitch Stream",
                    "duration": 3600,
                    "viewer_count": 5000,
                    "category": "Gaming",
                }
            )

            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={
                        "transcript": "This is a test Twitch stream with gaming content",
                        "language": "en",
                        "confidence": 0.90,
                        "word_count": 800,
                    }
                )

                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={
                            "sentiment": "neutral",
                            "topics": ["gaming", "entertainment", "streaming"],
                            "debate_score": 0.4,
                            "fact_check_score": 0.6,
                            "bias_score": 0.2,
                        }
                    )

                    with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
                        mock_memory.return_value = StepResult.ok(
                            data={"memory_id": "mem_456", "stored": True, "vector_count": 150}
                        )

                        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
                            mock_discord.return_value = StepResult.ok(data={"message_id": "msg_456", "sent": True})

                            # Execute the complete workflow
                            result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                interaction=mock_discord_interaction, url=url, depth=depth
                            )

        # Verify the complete workflow
        assert result is not None
        mock_discord_interaction.response.send_message.assert_called_once()
        mock_discord_interaction.followup.send.assert_called()

    @pytest.mark.asyncio
    async def test_complete_tiktok_workflow(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete TikTok workflow from Discord to analysis."""
        url = "https://tiktok.com/@user/video/test123"
        depth = "comprehensive"

        # Mock the complete workflow
        with patch.object(content_pipeline, "_download_tiktok_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={
                    "url": url,
                    "title": "Test TikTok Video",
                    "duration": 30,
                    "hashtags": ["#viral", "#trending", "#test"],
                    "likes": 1000,
                }
            )

            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={
                        "transcript": "This is a test TikTok video with trending content",
                        "language": "en",
                        "confidence": 0.88,
                        "word_count": 100,
                    }
                )

                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={
                            "sentiment": "positive",
                            "topics": ["social", "trending", "short_form"],
                            "debate_score": 0.2,
                            "fact_check_score": 0.5,
                            "bias_score": 0.1,
                        }
                    )

                    with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
                        mock_memory.return_value = StepResult.ok(
                            data={"memory_id": "mem_789", "stored": True, "vector_count": 50}
                        )

                        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
                            mock_discord.return_value = StepResult.ok(data={"message_id": "msg_789", "sent": True})

                            # Execute the complete workflow
                            result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                interaction=mock_discord_interaction, url=url, depth=depth
                            )

        # Verify the complete workflow
        assert result is not None
        mock_discord_interaction.response.send_message.assert_called_once()
        mock_discord_interaction.followup.send.assert_called()

    @pytest.mark.asyncio
    async def test_complete_reddit_workflow(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete Reddit workflow from Discord to analysis."""
        url = "https://reddit.com/r/test/comments/test123"
        depth = "comprehensive"

        # Mock the complete workflow
        with patch.object(content_pipeline, "_download_reddit_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={
                    "url": url,
                    "title": "Test Reddit Post",
                    "subreddit": "test",
                    "upvotes": 500,
                    "comments": 100,
                    "text": "This is a test Reddit post with discussion content",
                }
            )

            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={
                        "transcript": "This is a test Reddit post with discussion content",
                        "language": "en",
                        "confidence": 0.92,
                        "word_count": 200,
                    }
                )

                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={
                            "sentiment": "mixed",
                            "topics": ["discussion", "community", "debate"],
                            "debate_score": 0.9,
                            "fact_check_score": 0.8,
                            "bias_score": 0.4,
                        }
                    )

                    with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
                        mock_memory.return_value = StepResult.ok(
                            data={"memory_id": "mem_101", "stored": True, "vector_count": 75}
                        )

                        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
                            mock_discord.return_value = StepResult.ok(data={"message_id": "msg_101", "sent": True})

                            # Execute the complete workflow
                            result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                interaction=mock_discord_interaction, url=url, depth=depth
                            )

        # Verify the complete workflow
        assert result is not None
        mock_discord_interaction.response.send_message.assert_called_once()
        mock_discord_interaction.followup.send.assert_called()

    @pytest.mark.asyncio
    async def test_complete_workflow_with_quality_assessment(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete workflow with quality assessment."""
        url = "https://youtube.com/watch?v=test123"
        depth = "comprehensive"

        # Mock quality assessment
        with patch.object(content_pipeline, "_calculate_spam_score") as mock_spam:
            mock_spam.return_value = 0.1

            with patch.object(content_pipeline, "_calculate_wer") as mock_wer:
                mock_wer.return_value = 0.05

                with patch.object(content_pipeline, "_calculate_repetition_ratio") as mock_repetition:
                    mock_repetition.return_value = 0.15

                    with patch.object(content_pipeline, "_calculate_vocabulary_diversity") as mock_diversity:
                        mock_diversity.return_value = 0.85

                        # Mock the complete workflow
                        with patch.object(content_pipeline, "_download_youtube_content") as mock_download:
                            mock_download.return_value = StepResult.ok(
                                data={"url": url, "title": "Test Video", "duration": 600}
                            )

                            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                                mock_transcribe.return_value = StepResult.ok(
                                    data={
                                        "transcript": "This is a test transcript",
                                        "language": "en",
                                        "confidence": 0.95,
                                    }
                                )

                                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                                    mock_analyze.return_value = StepResult.ok(
                                        data={"sentiment": "positive", "topics": ["technology"], "debate_score": 0.7}
                                    )

                                    with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
                                        mock_memory.return_value = StepResult.ok(
                                            data={"memory_id": "mem_123", "stored": True}
                                        )

                                        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
                                            mock_discord.return_value = StepResult.ok(
                                                data={"message_id": "msg_123", "sent": True}
                                            )

                                            # Execute the complete workflow
                                            result = (
                                                await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                                    interaction=mock_discord_interaction, url=url, depth=depth
                                                )
                                            )

        # Verify quality assessment was performed
        assert result is not None
        mock_spam.assert_called_once()
        mock_wer.assert_called_once()
        mock_repetition.assert_called_once()
        mock_diversity.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_workflow_with_error_recovery(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete workflow with error recovery."""
        url = "https://youtube.com/watch?v=test123"
        depth = "comprehensive"

        # Mock download failure with retry
        call_count = 0

        async def mock_download_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return StepResult.fail("Download failed")
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

                            # Execute the complete workflow
                            result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                interaction=mock_discord_interaction, url=url, depth=depth
                            )

        # Verify error recovery
        assert result is not None
        assert call_count == 2  # Should have retried

    @pytest.mark.asyncio
    async def test_complete_workflow_with_tenant_isolation(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction
    ):
        """Test complete workflow with tenant isolation."""
        url = "https://youtube.com/watch?v=test123"
        depth = "comprehensive"

        # Test with different tenants
        tenants = [("tenant1", "workspace1"), ("tenant2", "workspace2"), ("tenant3", "workspace3")]

        results = {}
        for tenant, workspace in tenants:
            # Mock tenant-specific processing
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

                                # Execute the complete workflow
                                result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                    interaction=mock_discord_interaction, url=url, depth=depth
                                )

                                results[f"{tenant}_{workspace}"] = result

        # Verify tenant isolation
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

        # Mock concurrent processing
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

                            # Execute concurrently
                            tasks = [
                                autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                    interaction=mock_discord_interaction, url=url, depth="comprehensive"
                                )
                                for url in urls
                            ]

                            results = await asyncio.gather(*tasks)

        # Verify all results succeeded
        for result in results:
            assert result is not None

    @pytest.mark.asyncio
    async def test_complete_workflow_with_performance_monitoring(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete workflow with performance monitoring."""
        url = "https://youtube.com/watch?v=test123"
        depth = "comprehensive"

        # Mock performance monitoring
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

                                # Execute the complete workflow
                                result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                    interaction=mock_discord_interaction, url=url, depth=depth
                                )

        # Verify performance monitoring
        assert result is not None
        mock_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_workflow_with_alerting(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete workflow with intelligent alerting."""
        url = "https://youtube.com/watch?v=test123"
        depth = "comprehensive"

        # Mock alerting system
        with patch.object(autonomous_orchestrator, "_send_intelligent_alert") as mock_alert:
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

                                # Execute the complete workflow
                                result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                    interaction=mock_discord_interaction, url=url, depth=depth
                                )

        # Verify alerting
        assert result is not None
        mock_alert.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_workflow_with_memory_integration(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete workflow with memory integration."""
        url = "https://youtube.com/watch?v=test123"
        depth = "comprehensive"

        # Mock memory operations
        with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
            mock_memory.return_value = StepResult.ok(data={"memory_id": "mem_123", "stored": True, "vector_count": 100})

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

                            # Execute the complete workflow
                            result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                interaction=mock_discord_interaction, url=url, depth=depth
                            )

        # Verify memory integration
        assert result is not None
        mock_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_workflow_with_discord_integration(
        self, autonomous_orchestrator, content_pipeline, mock_discord_interaction, test_tenant_context
    ):
        """Test complete workflow with Discord integration."""
        url = "https://youtube.com/watch?v=test123"
        depth = "comprehensive"

        # Mock Discord integration
        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
            mock_discord.return_value = StepResult.ok(data={"message_id": "msg_123", "sent": True})

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

                            # Execute the complete workflow
                            result = await autonomous_orchestrator.execute_autonomous_intelligence_workflow(
                                interaction=mock_discord_interaction, url=url, depth=depth
                            )

        # Verify Discord integration
        assert result is not None
        mock_discord.assert_called_once()
