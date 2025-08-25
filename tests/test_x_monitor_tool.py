from ultimate_discord_intelligence_bot.tools.x_monitor_tool import XMonitorTool


def test_x_monitor_tool_filters_seen_posts():
    tool = XMonitorTool()
    posts = [
        {"id": "1", "url": "https://x.com/a", "author": "alice", "timestamp": "1"},
        {"id": "2", "url": "https://x.com/b", "author": "bob", "timestamp": "2"},
    ]
    first = tool._run(posts)
    assert len(first["new_posts"]) == 2
    second = tool._run(posts)
    assert len(second["new_posts"]) == 0
