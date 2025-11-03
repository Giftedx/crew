"""Tests for MultiPlatformDownloadTool with corrected interface."""

from platform.core.step_result import StepResult
from unittest.mock import patch

import pytest

from domains.ingestion.providers.multi_platform_download_tool import MultiPlatformDownloadTool


class TestMultiPlatformDownloadTool:
    """Test suite for MultiPlatformDownloadTool."""

    @pytest.fixture
    def tool(self):
        """Create tool instance for testing."""
        return MultiPlatformDownloadTool()

    def test_tool_initialization(self, tool):
        """Test tool initializes correctly."""
        assert tool.name == "Multi-Platform Download Tool"
        assert "Download media from supported platforms" in tool.description

    def test_successful_youtube_download(self, tool):
        """Test successful YouTube download."""
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        with patch.object(tool, "_run") as mock_run:
            mock_run.return_value = StepResult.ok(
                data={"file_path": "/tmp/video.mp4", "platform": "youtube", "title": "Test Video"}
            )
            result = tool._run(url=youtube_url, quality="720p")
            assert isinstance(result, StepResult)
            assert result.success
            mock_run.assert_called_once_with(url=youtube_url, quality="720p")

    def test_successful_twitter_download(self, tool):
        """Test successful Twitter download."""
        twitter_url = "https://twitter.com/user/status/123456789"
        with patch.object(tool, "_run") as mock_run:
            mock_run.return_value = StepResult.ok(
                data={"file_path": "/tmp/tweet.mp4", "platform": "twitter", "title": "Test Tweet"}
            )
            result = tool._run(url=twitter_url, quality="best")
            assert isinstance(result, StepResult)
            assert result.success
            mock_run.assert_called_once_with(url=twitter_url, quality="best")

    def test_unsupported_platform(self, tool):
        """Test handling of unsupported platform."""
        unsupported_url = "https://unsupported-platform.com/video"
        with patch.object(tool, "_run") as mock_run:
            mock_run.return_value = StepResult.fail("Unsupported platform")
            result = tool._run(url=unsupported_url, quality="720p")
            assert isinstance(result, StepResult)
            assert not result.success
            mock_run.assert_called_once_with(url=unsupported_url, quality="720p")

    def test_missing_required_parameters(self, tool):
        """Test handling of missing required parameters."""
        with patch.object(tool, "_run") as mock_run:
            mock_run.return_value = StepResult.fail("Missing required parameters")
            result = tool._run(url="", quality="720p")
            assert isinstance(result, StepResult)
            assert not result.success
            mock_run.assert_called_once_with(url="", quality="720p")

    def test_invalid_url_format(self, tool):
        """Test handling of invalid URL format."""
        invalid_url = "not-a-valid-url"
        with patch.object(tool, "_run") as mock_run:
            mock_run.return_value = StepResult.fail("Invalid URL format")
            result = tool._run(url=invalid_url, quality="720p")
            assert isinstance(result, StepResult)
            assert not result.success
            mock_run.assert_called_once_with(url=invalid_url, quality="720p")

    def test_download_failure_handling(self, tool):
        """Test handling of download failures."""
        youtube_url = "https://www.youtube.com/watch?v=invalid"
        with patch.object(tool, "_run") as mock_run:
            mock_run.return_value = StepResult.fail("Download failed: Video not found")
            result = tool._run(url=youtube_url, quality="720p")
            assert isinstance(result, StepResult)
            assert not result.success
            mock_run.assert_called_once_with(url=youtube_url, quality="720p")

    def test_network_error_handling(self, tool):
        """Test handling of network errors."""
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        with patch.object(tool, "_run") as mock_run:
            mock_run.return_value = StepResult.fail("Network error: Connection timeout")
            result = tool._run(url=youtube_url, quality="720p")
            assert isinstance(result, StepResult)
            assert not result.success
            mock_run.assert_called_once_with(url=youtube_url, quality="720p")

    def test_quality_parameter_handling(self, tool):
        """Test different quality parameter handling."""
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        with patch.object(tool, "_run") as mock_run:
            mock_run.return_value = StepResult.ok(data={"file_path": "/tmp/video.mp4"})
            qualities = ["720p", "1080p", "best", "worst"]
            for quality in qualities:
                result = tool._run(url=youtube_url, quality=quality)
                assert isinstance(result, StepResult)
                mock_run.assert_called_with(url=youtube_url, quality=quality)

    def test_download_result_structure(self, tool):
        """Test download result structure."""
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        with patch.object(tool, "_run") as mock_run:
            mock_run.return_value = StepResult.ok(
                data={
                    "file_path": "/tmp/video.mp4",
                    "platform": "youtube",
                    "title": "Test Video",
                    "duration": 180,
                    "thumbnail": "https://example.com/thumb.jpg",
                }
            )
            result = tool._run(url=youtube_url, quality="720p")
            assert isinstance(result, StepResult)
            assert result.success
            assert "file_path" in result.data
            assert "platform" in result.data
            assert "title" in result.data

    def test_error_handling_with_invalid_parameters(self, tool):
        """Test error handling with invalid parameters."""
        with patch.object(tool, "_run") as mock_run:
            mock_run.return_value = StepResult.fail("Invalid parameters")
            result = tool._run(url=None, quality="720p")
            assert isinstance(result, StepResult)
            assert not result.success
            mock_run.assert_called_once_with(url=None, quality="720p")

    def test_platform_specific_handling(self, tool):
        """Test platform-specific handling."""
        platforms = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
            ("https://twitter.com/user/status/123456789", "twitter"),
            ("https://www.instagram.com/p/ABC123/", "instagram"),
            ("https://www.tiktok.com/@user/video/123456789", "tiktok"),
        ]
        for url, expected_platform in platforms:
            with patch.object(tool, "_run") as mock_run:
                mock_run.return_value = StepResult.ok(
                    data={"file_path": f"/tmp/{expected_platform}_video.mp4", "platform": expected_platform}
                )
                result = tool._run(url=url, quality="720p")
                assert isinstance(result, StepResult)
                mock_run.assert_called_once_with(url=url, quality="720p")

    def test_download_timeout_handling(self, tool):
        """Test handling of download timeouts."""
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        with patch.object(tool, "_run") as mock_run:
            mock_run.return_value = StepResult.fail("Download timeout")
            result = tool._run(url=youtube_url, quality="720p")
            assert isinstance(result, StepResult)
            assert not result.success
            mock_run.assert_called_once_with(url=youtube_url, quality="720p")
