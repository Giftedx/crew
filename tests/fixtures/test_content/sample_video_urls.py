"""Sample video URLs for testing."""

# Test URLs for different platforms
SAMPLE_VIDEO_URLS = {
    "youtube": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "twitch": "https://www.twitch.tv/videos/1234567890",
    "tiktok": "https://www.tiktok.com/@user/video/1234567890",
    "twitter": "https://twitter.com/user/status/1234567890",
    "instagram": "https://www.instagram.com/p/ABC123/",
    "reddit": "https://www.reddit.com/r/videos/comments/abc123/test_video/",
}

# Test content for analysis
SAMPLE_TRANSCRIPTS = {
    "short": "This is a short test transcript for basic analysis.",
    "medium": "This is a medium-length transcript that contains multiple sentences and provides more content for analysis. It includes various topics and should trigger different analysis tools.",
    "long": "This is a much longer transcript that contains extensive content for comprehensive analysis. It includes multiple paragraphs, various topics, sentiment changes, and should provide rich data for testing the full analysis pipeline. The content covers different subjects and should trigger various analysis tools and provide comprehensive insights.",
}

# Sample analysis results
SAMPLE_ANALYSIS_RESULTS = {
    "sentiment": {"positive": 0.7, "negative": 0.1, "neutral": 0.2},
    "topics": ["technology", "artificial intelligence", "automation"],
    "key_phrases": ["machine learning", "data analysis", "automation"],
    "summary": "This content discusses the impact of artificial intelligence on modern technology and automation processes.",
}
