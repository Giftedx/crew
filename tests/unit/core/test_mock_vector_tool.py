import unittest

from ultimate_discord_intelligence_bot.tools.mock_vector_tool import (
    MockVectorSearchTool,
)


class TestMockVectorSearchTool(unittest.TestCase):
    def setUp(self):
        self.tool = MockVectorSearchTool()

    def test_run(self):
        # Arrange
        query = "The Earth approximately spherical"

        # Act
        result = self.tool.run(query)

        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["topic"], "geography")


if __name__ == "__main__":
    unittest.main()
