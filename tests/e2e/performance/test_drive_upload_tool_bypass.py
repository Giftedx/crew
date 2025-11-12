import unittest

from ultimate_discord_intelligence_bot.tools.integration.drive_upload_tool_bypass import (
    DriveUploadTool,
)


class TestDriveUploadToolBypass(unittest.TestCase):
    def test_run(self):
        # Arrange
        tool = DriveUploadTool()
        file_path = "/path/to/file.txt"
        platform = "test_platform"

        # Act
        result = tool.run(file_path, platform)

        # Assert
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(
            result["message"],
            "Google Drive uploads disabled (no credentials configured)",
        )
        self.assertEqual(result["file_path"], file_path)
        self.assertEqual(result["platform"], platform)


if __name__ == "__main__":
    unittest.main()
