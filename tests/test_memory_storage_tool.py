from unittest.mock import MagicMock

from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool


def test_memory_storage_tool_upsert_called():
    client = MagicMock()
    client.get_collection.side_effect = Exception()
    client.recreate_collection.return_value = None
    client.upsert.return_value = None

    tool = MemoryStorageTool(client=client, embedding_fn=lambda t: [0.1])
    result = tool.run("hello", {"meta": 1})

    assert result["status"] == "success"
    client.recreate_collection.assert_called_once()
    client.upsert.assert_called_once()
