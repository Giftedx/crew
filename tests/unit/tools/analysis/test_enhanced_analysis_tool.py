import unittest

from ultimate_discord_intelligence_bot.tools.enhanced_analysis_tool import (
    EnhancedAnalysisTool,
)


class TestEnhancedAnalysisTool(unittest.TestCase):
    def setUp(self):
        self.tool = EnhancedAnalysisTool()

    def test_political_analysis(self):
        # Arrange
        text = "This is a test of the political analysis tool. It should detect healthcare and economy keywords."

        # Act
        result = self.tool._political_analysis(text)

        # Assert
        self.assertIn("healthcare", result["political_topics"])
        self.assertIn("economy", result["political_topics"])

    def test_sentiment_analysis(self):
        # Arrange
        text = "This is a good test of the sentiment analysis tool. It should detect a positive sentiment."

        # Act
        result = self.tool._sentiment_analysis(text)

        # Assert
        self.assertEqual(result["sentiment"], "positive")

    def test_claim_extraction(self):
        # Arrange
        text = "This is a test of the claim extraction tool. It should extract the claim that X is Y."

        # Act
        result = self.tool._claim_extraction(text)

        # Assert
        self.assertIn("X is Y", result["extracted_claims"])

    def test_run_with_string_input(self):
        # Arrange
        text = "This is a good test of the run method with a string input. It should detect a positive sentiment."

        # Act
        result = self.tool.run(text)

        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["sentiment"], "positive")

    def test_run_with_dict_input(self):
        # Arrange
        content = {
            "title": "This is a good test",
            "description": "of the run method with a dict input.",
            "url": "https://example.com",
            "platform": "test_platform",
        }

        # Act
        result = self.tool.run(content)

        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["sentiment"], "positive")


if __name__ == "__main__":
    unittest.main()
