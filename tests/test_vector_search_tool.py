from unittest.mock import MagicMock

from ultimate_discord_intelligence_bot.tools.vector_search_tool import VectorSearchTool


def test_vector_search_tool_queries_client():
    client = MagicMock()
    client.get_collection.return_value = None
    client.search.return_value = [MagicMock(payload={"text": "hello"})]

    tool = VectorSearchTool(client=client, embedding_fn=lambda t: [0.1])
    results = tool.run("hi", limit=1, collection="analysis")

    assert results == [{"text": "hello"}]
    client.search.assert_called_once()
    args, kwargs = client.search.call_args
    assert kwargs.get("collection_name") == "analysis"
