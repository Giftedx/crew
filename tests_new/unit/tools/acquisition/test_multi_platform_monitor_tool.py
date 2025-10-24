from ultimate_discord_intelligence_bot.tools.multi_platform_monitor_tool import (
    MultiPlatformMonitorTool,
)


def test_monitor_filters_seen_items():
    tool = MultiPlatformMonitorTool()
    first_batch = [{"id": "1", "url": "https://youtu.be/1"}]
    second_batch = [
        {"id": "1", "url": "https://youtu.be/1"},
        {"id": "2", "url": "https://kick.com/2"},
    ]

    first = tool._run(first_batch)
    assert first["new_items"] == first_batch

    second = tool._run(second_batch)
    assert second["new_items"] == [second_batch[1]]
