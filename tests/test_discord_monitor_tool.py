from ultimate_discord_intelligence_bot.tools.discord_monitor_tool import DiscordMonitorTool


def test_discord_monitor_tool_filters_seen_messages():
    tool = DiscordMonitorTool()
    messages = [
        {"id": "m1", "url": "https://discord.com/ch/1", "author": "mod", "timestamp": "1"},
        {"id": "m2", "url": "https://discord.com/ch/2", "author": "user", "timestamp": "2"},
    ]
    first = tool._run(messages)
    assert len(first["new_messages"]) == 2
    second = tool._run(messages)
    assert len(second["new_messages"]) == 0
