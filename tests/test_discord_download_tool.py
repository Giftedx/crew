import os
import unittest
from unittest.mock import MagicMock, patch

from ultimate_discord_intelligence_bot.tools.discord_download_tool import DiscordDownloadTool


class TestDiscordDownloadTool(unittest.TestCase):
    @patch("ultimate_discord_intelligence_bot.tools.discord_download_tool.resilient_get")
    def test_run_success(self, mock_resilient_get):
        # Arrange
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"test content"]
        mock_resilient_get.return_value = mock_response

        tool = DiscordDownloadTool()
        url = "https://cdn.discordapp.com/attachments/1234567890/1234567890/test.txt"

        # Act
        result = tool.run(url)

        # Assert
        self.assertEqual(result["status"], "success")
        self.assertTrue(os.path.exists(result["local_path"]))
        with open(result["local_path"], "rb") as f:
            self.assertEqual(f.read(), b"test content")

        # Clean up
        os.remove(result["local_path"])

    @patch("ultimate_discord_intelligence_bot.tools.discord_download_tool.resilient_get")
    def test_run_error(self, mock_resilient_get):
        # Arrange
        mock_resilient_get.side_effect = Exception("Test error")

        tool = DiscordDownloadTool()
        url = "https://cdn.discordapp.com/attachments/1234567890/1234567890/test.txt"

        # Act
        result = tool.run(url)

        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "Test error")


if __name__ == "__main__":
    unittest.main()
