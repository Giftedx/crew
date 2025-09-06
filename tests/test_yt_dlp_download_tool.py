
import unittest
from unittest.mock import MagicMock, patch

from ultimate_discord_intelligence_bot.tools.yt_dlp_download_tool import YtDlpDownloadTool


class TestYtDlpDownloadTool(unittest.TestCase):
    @patch("subprocess.run")
    def test_download_success(self, mock_run):
        # Arrange
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = '{"title": "Test Video", "id": "12345", "filepath": "/path/to/video.mp4"}'
        mock_run.return_value = mock_process

        tool = YtDlpDownloadTool()
        url = "https://www.youtube.com/watch?v=12345"

        # Act
        result = tool.run(url)

        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["title"], "Test Video")
        self.assertEqual(result["video_id"], "12345")
        self.assertEqual(result["local_path"], "/path/to/video.mp4")

    @patch("subprocess.run")
    def test_download_already_downloaded(self, mock_run):
        # Arrange
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = '[download] /path/to/video.mp4 has already been downloaded'
        mock_run.return_value = mock_process

        tool = YtDlpDownloadTool()
        url = "https://www.youtube.com/watch?v=12345"

        # Act
        result = tool.run(url)

        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["note"], "File was already downloaded")

    @patch("subprocess.run")
    def test_download_error(self, mock_run):
        # Arrange
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "Test error"
        mock_run.return_value = mock_process

        tool = YtDlpDownloadTool()
        url = "https://www.youtube.com/watch?v=12345"

        # Act
        result = tool.run(url)

        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "Test error")


if __name__ == "__main__":
    unittest.main()
