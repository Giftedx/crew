"""Tests for the sentiment analysis tool."""

from ultimate_discord_intelligence_bot.tools.sentiment_tool import SentimentTool


def test_sentiment_tool_classifies_text():
    tool = SentimentTool()
    pos = tool.run("I love this awesome show")
    neg = tool.run("This is terrible and bad")
    assert pos["sentiment"] == "positive"
    assert neg["sentiment"] == "negative"
