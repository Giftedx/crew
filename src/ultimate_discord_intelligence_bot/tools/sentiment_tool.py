"""Compatibility shim for the sentiment analysis tool.

This module preserves the historic import path
``ultimate_discord_intelligence_bot.tools.sentiment_tool`` while delegating to
the relocated implementation in :mod:`domains.intelligence.analysis`.
"""

from domains.intelligence.analysis.sentiment_tool import SentimentTool


__all__ = ["SentimentTool"]
