import unittest
from unittest.mock import MagicMock, patch

from ultimate_discord_intelligence_bot.tools.enhanced_youtube_tool import (
    EnhancedYouTubeDownloadTool,
)


class TestEnhancedYouTubeDownloadTool(unittest.TestCase):
    @patch("shutil.which")
    def test_ytdlp_available(self, mock_which):
        # Arrange
        mock_which.return_value = "/usr/bin/yt-dlp"
        tool = EnhancedYouTubeDownloadTool()

        # Assert
        self.assertTrue(tool.ytdlp_available)

    @patch("shutil.which")
    def test_ytdlp_not_available(self, mock_which):
        # Arrange
        mock_which.return_value = None
        tool = EnhancedYouTubeDownloadTool()

        # Assert
        self.assertFalse(tool.ytdlp_available)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_download_with_ytdlp_success(self, mock_which, mock_run):
        # Arrange
        mock_which.return_value = "/usr/bin/yt-dlp"
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = '{"title": "Test Video", "description": "Test description"}'
        mock_run.return_value = mock_process

        tool = EnhancedYouTubeDownloadTool()
        url = "https://www.youtube.com/watch?v=12345"

        # Act
        result = tool.run(url)

        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["title"], "Test Video")

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_download_with_ytdlp_error(self, mock_which, mock_run):
        # Arrange
        mock_which.return_value = "/usr/bin/yt-dlp"
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "Test error"
        mock_run.return_value = mock_process

        tool = EnhancedYouTubeDownloadTool()
        url = "https://www.youtube.com/watch?v=12345"

        # Act
        result = tool.run(url)

        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "yt-dlp failed: Test error")

    @patch("shutil.which")
    def test_extract_metadata_only(self, mock_which):
        # Arrange
        mock_which.return_value = None
        tool = EnhancedYouTubeDownloadTool()
        url = "https://www.youtube.com/watch?v=12345"

        # Act
        result = tool.run(url)

        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["title"], "YouTube Video 12345")


if __name__ == "__main__":
    unittest.main()
