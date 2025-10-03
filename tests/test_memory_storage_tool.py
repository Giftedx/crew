from unittest.mock import MagicMock

from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool


def test_memory_storage_tool_upsert_called():
    client = MagicMock()
    client.get_collection.side_effect = Exception()
    client.recreate_collection.return_value = None
    client.upsert.return_value = None

    # Use multi-dimension embedding (Fix #6: single-dimension vectors are rejected)
    tool = MemoryStorageTool(client=client, embedding_fn=lambda t: [0.1, 0.2, 0.3])
    result = tool.run("hello", {"meta": 1}, collection="analysis")

    assert result["status"] == "success"
    assert client.recreate_collection.call_count == 2
    client.upsert.assert_called_once()
