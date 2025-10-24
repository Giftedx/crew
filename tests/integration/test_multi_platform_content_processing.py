"""Integration tests for multi-platform content processing workflows."""

import asyncio
from unittest.mock import patch

import pytest

from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext


class TestMultiPlatformContentProcessing:
    """Integration tests for multi-platform content processing."""

    @pytest.fixture
    def content_pipeline(self):
        """Create a ContentPipeline instance."""
        return ContentPipeline()

    @pytest.fixture
    def test_tenant_context(self):
        """Create a test tenant context."""
        return TenantContext(tenant="test_tenant", workspace="test_workspace")

    @pytest.fixture
    def test_urls(self):
        """Test URLs for different platforms."""
        return {
            "youtube": "https://youtube.com/watch?v=test123",
            "twitch": "https://twitch.tv/videos/test123",
            "tiktok": "https://tiktok.com/@user/video/test123",
            "reddit": "https://reddit.com/r/test/comments/test123",
            "rumble": "https://rumble.com/vtest123",
            "bitchute": "https://bitchute.com/video/test123",
            "odysee": "https://odysee.com/@user/test123",
            "kick": "https://kick.com/user/video/test123",
            "x": "https://x.com/user/status/test123",
        }

    @pytest.mark.asyncio
    async def test_youtube_content_processing(self, content_pipeline, test_tenant_context):
        """Test YouTube content processing workflow."""
        url = "https://youtube.com/watch?v=test123"

        # Mock YouTube-specific processing
        with patch.object(content_pipeline, "_download_youtube_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={"url": url, "title": "Test Video", "duration": 300, "quality": "720p"}
            )

            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={"transcript": "This is a test transcript", "language": "en", "confidence": 0.95}
                )

                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={"sentiment": "positive", "topics": ["technology", "AI"], "debate_score": 0.7}
                    )

                    result = await content_pipeline.process_content(
                        url=url, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
                    )

        # Verify processing steps
        assert result.success
        assert "youtube" in result.data.get("platform", "").lower()

    @pytest.mark.asyncio
    async def test_twitch_content_processing(self, content_pipeline, test_tenant_context):
        """Test Twitch content processing workflow."""
        url = "https://twitch.tv/videos/test123"

        # Mock Twitch-specific processing
        with patch.object(content_pipeline, "_download_twitch_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={"url": url, "title": "Test Stream", "duration": 1800, "viewer_count": 1000}
            )

            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={"transcript": "This is a test stream transcript", "language": "en", "confidence": 0.90}
                )

                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={"sentiment": "neutral", "topics": ["gaming", "entertainment"], "debate_score": 0.3}
                    )

                    result = await content_pipeline.process_content(
                        url=url, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
                    )

        # Verify processing steps
        assert result.success
        assert "twitch" in result.data.get("platform", "").lower()

    @pytest.mark.asyncio
    async def test_tiktok_content_processing(self, content_pipeline, test_tenant_context):
        """Test TikTok content processing workflow."""
        url = "https://tiktok.com/@user/video/test123"

        # Mock TikTok-specific processing
        with patch.object(content_pipeline, "_download_tiktok_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={"url": url, "title": "Test TikTok", "duration": 60, "hashtags": ["#test", "#viral"]}
            )

            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={"transcript": "This is a test TikTok transcript", "language": "en", "confidence": 0.88}
                )

                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={"sentiment": "positive", "topics": ["social", "trending"], "debate_score": 0.2}
                    )

                    result = await content_pipeline.process_content(
                        url=url, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
                    )

        # Verify processing steps
        assert result.success
        assert "tiktok" in result.data.get("platform", "").lower()

    @pytest.mark.asyncio
    async def test_reddit_content_processing(self, content_pipeline, test_tenant_context):
        """Test Reddit content processing workflow."""
        url = "https://reddit.com/r/test/comments/test123"

        # Mock Reddit-specific processing
        with patch.object(content_pipeline, "_download_reddit_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={"url": url, "title": "Test Reddit Post", "subreddit": "test", "upvotes": 100, "comments": 50}
            )

            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={"transcript": "This is a test Reddit post content", "language": "en", "confidence": 0.92}
                )

                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={"sentiment": "mixed", "topics": ["discussion", "community"], "debate_score": 0.8}
                    )

                    result = await content_pipeline.process_content(
                        url=url, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
                    )

        # Verify processing steps
        assert result.success
        assert "reddit" in result.data.get("platform", "").lower()

    @pytest.mark.asyncio
    async def test_rumble_content_processing(self, content_pipeline, test_tenant_context):
        """Test Rumble content processing workflow."""
        url = "https://rumble.com/vtest123"

        # Mock Rumble-specific processing
        with patch.object(content_pipeline, "_download_rumble_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={"url": url, "title": "Test Rumble Video", "duration": 600, "views": 5000}
            )

            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={"transcript": "This is a test Rumble video transcript", "language": "en", "confidence": 0.89}
                )

                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={"sentiment": "neutral", "topics": ["alternative", "independent"], "debate_score": 0.6}
                    )

                    result = await content_pipeline.process_content(
                        url=url, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
                    )

        # Verify processing steps
        assert result.success
        assert "rumble" in result.data.get("platform", "").lower()

    @pytest.mark.asyncio
    async def test_bitchute_content_processing(self, content_pipeline, test_tenant_context):
        """Test BitChute content processing workflow."""
        url = "https://bitchute.com/video/test123"

        # Mock BitChute-specific processing
        with patch.object(content_pipeline, "_download_bitchute_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={"url": url, "title": "Test BitChute Video", "duration": 900, "views": 2000}
            )

            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={
                        "transcript": "This is a test BitChute video transcript",
                        "language": "en",
                        "confidence": 0.87,
                    }
                )

                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={"sentiment": "neutral", "topics": ["alternative", "free_speech"], "debate_score": 0.7}
                    )

                    result = await content_pipeline.process_content(
                        url=url, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
                    )

        # Verify processing steps
        assert result.success
        assert "bitchute" in result.data.get("platform", "").lower()

    @pytest.mark.asyncio
    async def test_odysee_content_processing(self, content_pipeline, test_tenant_context):
        """Test Odysee content processing workflow."""
        url = "https://odysee.com/@user/test123"

        # Mock Odysee-specific processing
        with patch.object(content_pipeline, "_download_odysee_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={"url": url, "title": "Test Odysee Video", "duration": 1200, "views": 3000}
            )

            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={"transcript": "This is a test Odysee video transcript", "language": "en", "confidence": 0.91}
                )

                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={"sentiment": "positive", "topics": ["decentralized", "blockchain"], "debate_score": 0.5}
                    )

                    result = await content_pipeline.process_content(
                        url=url, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
                    )

        # Verify processing steps
        assert result.success
        assert "odysee" in result.data.get("platform", "").lower()

    @pytest.mark.asyncio
    async def test_kick_content_processing(self, content_pipeline, test_tenant_context):
        """Test Kick content processing workflow."""
        url = "https://kick.com/user/video/test123"

        # Mock Kick-specific processing
        with patch.object(content_pipeline, "_download_kick_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={"url": url, "title": "Test Kick Stream", "duration": 2400, "viewer_count": 500}
            )

            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={"transcript": "This is a test Kick stream transcript", "language": "en", "confidence": 0.86}
                )

                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={"sentiment": "neutral", "topics": ["streaming", "gaming"], "debate_score": 0.4}
                    )

                    result = await content_pipeline.process_content(
                        url=url, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
                    )

        # Verify processing steps
        assert result.success
        assert "kick" in result.data.get("platform", "").lower()

    @pytest.mark.asyncio
    async def test_x_content_processing(self, content_pipeline, test_tenant_context):
        """Test X (Twitter) content processing workflow."""
        url = "https://x.com/user/status/test123"

        # Mock X-specific processing
        with patch.object(content_pipeline, "_download_x_content") as mock_download:
            mock_download.return_value = StepResult.ok(
                data={"url": url, "title": "Test X Post", "text": "This is a test post", "likes": 100, "retweets": 50}
            )

            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={"transcript": "This is a test X post content", "language": "en", "confidence": 0.94}
                )

                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={"sentiment": "positive", "topics": ["social", "microblogging"], "debate_score": 0.3}
                    )

                    result = await content_pipeline.process_content(
                        url=url, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
                    )

        # Verify processing steps
        assert result.success
        assert "x" in result.data.get("platform", "").lower()

    @pytest.mark.asyncio
    async def test_cross_platform_content_processing(self, content_pipeline, test_tenant_context, test_urls):
        """Test cross-platform content processing."""
        results = {}

        for platform, url in test_urls.items():
            # Mock platform-specific processing
            with patch.object(content_pipeline, f"_download_{platform}_content") as mock_download:
                mock_download.return_value = StepResult.ok(
                    data={"url": url, "title": f"Test {platform.title()} Content", "platform": platform}
                )

                with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                    mock_transcribe.return_value = StepResult.ok(
                        data={
                            "transcript": f"This is a test {platform} transcript",
                            "language": "en",
                            "confidence": 0.90,
                        }
                    )

                    with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                        mock_analyze.return_value = StepResult.ok(
                            data={"sentiment": "neutral", "topics": [platform, "content"], "debate_score": 0.5}
                        )

                        result = await content_pipeline.process_content(
                            url=url, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
                        )

                        results[platform] = result

        # Verify all platforms processed successfully
        for platform, result in results.items():
            assert result.success, f"Failed to process {platform} content"
            assert platform in result.data.get("platform", "").lower()

    @pytest.mark.asyncio
    async def test_content_processing_with_quality_metrics(self, content_pipeline, test_tenant_context):
        """Test content processing with quality metrics."""
        url = "https://youtube.com/watch?v=test123"

        # Mock quality metrics calculation
        with patch.object(content_pipeline, "_calculate_spam_score") as mock_spam:
            mock_spam.return_value = 0.1

            with patch.object(content_pipeline, "_calculate_wer") as mock_wer:
                mock_wer.return_value = 0.05

                with patch.object(content_pipeline, "_calculate_repetition_ratio") as mock_repetition:
                    mock_repetition.return_value = 0.15

                    with patch.object(content_pipeline, "_calculate_vocabulary_diversity") as mock_diversity:
                        mock_diversity.return_value = 0.85

                        with patch.object(content_pipeline, "_download_youtube_content") as mock_download:
                            mock_download.return_value = StepResult.ok(
                                data={"url": url, "title": "Test Video", "duration": 300}
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

                                    result = await content_pipeline.process_content(
                                        url=url,
                                        tenant=test_tenant_context.tenant,
                                        workspace=test_tenant_context.workspace,
                                    )

        # Verify quality metrics were calculated
        assert result.success
        assert "quality_metrics" in result.data

    @pytest.mark.asyncio
    async def test_content_processing_with_error_handling(self, content_pipeline, test_tenant_context):
        """Test content processing error handling."""
        url = "https://youtube.com/watch?v=test123"

        # Mock download failure
        with patch.object(content_pipeline, "_download_youtube_content") as mock_download:
            mock_download.return_value = StepResult.fail("Download failed")

            result = await content_pipeline.process_content(
                url=url, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
            )

        # Verify error handling
        assert not result.success
        assert "Download failed" in result.error

    @pytest.mark.asyncio
    async def test_content_processing_with_tenant_isolation(self, content_pipeline):
        """Test content processing with tenant isolation."""
        url = "https://youtube.com/watch?v=test123"

        # Test with different tenants
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

                        result = await content_pipeline.process_content(url=url, tenant=tenant, workspace=workspace)

                        results[f"{tenant}_{workspace}"] = result

        # Verify tenant isolation
        for key, result in results.items():
            assert result.success, f"Failed for tenant {key}"
            assert result.data.get("tenant") == key.split("_")[0]

    @pytest.mark.asyncio
    async def test_content_processing_with_concurrent_execution(self, content_pipeline, test_tenant_context):
        """Test content processing with concurrent execution."""
        urls = [
            "https://youtube.com/watch?v=test1",
            "https://youtube.com/watch?v=test2",
            "https://youtube.com/watch?v=test3",
        ]

        # Mock concurrent processing
        with patch.object(content_pipeline, "_download_youtube_content") as mock_download:
            mock_download.return_value = StepResult.ok(data={"url": "test", "title": "Test Video", "duration": 300})

            with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.return_value = StepResult.ok(
                    data={"transcript": "This is a test transcript", "language": "en", "confidence": 0.95}
                )

                with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                    mock_analyze.return_value = StepResult.ok(
                        data={"sentiment": "positive", "topics": ["technology"], "debate_score": 0.7}
                    )

                    # Execute concurrently
                    tasks = [
                        content_pipeline.process_content(
                            url=url, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
                        )
                        for url in urls
                    ]

                    results = await asyncio.gather(*tasks)

        # Verify all results succeeded
        for result in results:
            assert result.success

    @pytest.mark.asyncio
    async def test_content_processing_with_memory_integration(self, content_pipeline, test_tenant_context):
        """Test content processing with memory integration."""
        url = "https://youtube.com/watch?v=test123"

        # Mock memory operations
        with patch.object(content_pipeline, "_store_in_memory") as mock_memory:
            mock_memory.return_value = StepResult.ok(data={"memory_id": "mem_123", "stored": True})

            with patch.object(content_pipeline, "_download_youtube_content") as mock_download:
                mock_download.return_value = StepResult.ok(data={"url": url, "title": "Test Video", "duration": 300})

                with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                    mock_transcribe.return_value = StepResult.ok(
                        data={"transcript": "This is a test transcript", "language": "en", "confidence": 0.95}
                    )

                    with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                        mock_analyze.return_value = StepResult.ok(
                            data={"sentiment": "positive", "topics": ["technology"], "debate_score": 0.7}
                        )

                        result = await content_pipeline.process_content(
                            url=url, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
                        )

        # Verify memory integration
        assert result.success
        mock_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_content_processing_with_discord_integration(self, content_pipeline, test_tenant_context):
        """Test content processing with Discord integration."""
        url = "https://youtube.com/watch?v=test123"

        # Mock Discord integration
        with patch.object(content_pipeline, "_send_to_discord") as mock_discord:
            mock_discord.return_value = StepResult.ok(data={"message_id": "msg_123", "sent": True})

            with patch.object(content_pipeline, "_download_youtube_content") as mock_download:
                mock_download.return_value = StepResult.ok(data={"url": url, "title": "Test Video", "duration": 300})

                with patch.object(content_pipeline, "_transcribe_audio") as mock_transcribe:
                    mock_transcribe.return_value = StepResult.ok(
                        data={"transcript": "This is a test transcript", "language": "en", "confidence": 0.95}
                    )

                    with patch.object(content_pipeline, "_analyze_content") as mock_analyze:
                        mock_analyze.return_value = StepResult.ok(
                            data={"sentiment": "positive", "topics": ["technology"], "debate_score": 0.7}
                        )

                        result = await content_pipeline.process_content(
                            url=url, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
                        )

        # Verify Discord integration
        assert result.success
        mock_discord.assert_called_once()
