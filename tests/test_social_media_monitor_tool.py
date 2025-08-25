from ultimate_discord_intelligence_bot.tools.social_media_monitor_tool import (
    SocialMediaMonitorTool,
)


def test_social_media_monitor_tool_filters_posts():
    tool = SocialMediaMonitorTool()
    posts = {
        "twitter": ["Nothing here", "Keyword spotted"],
        "reddit": ["keyword appears twice", "another Keyword"],
        "discord": ["irrelevant"],
    }
    result = tool.run(posts, "keyword")
    assert result["status"] == "success"
    assert "twitter" in result["matches"]
    assert len(result["matches"]["reddit"]) == 2
    assert "discord" not in result["matches"]
