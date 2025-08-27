from ultimate_discord_intelligence_bot.services import MemoryService


def test_memory_service_store_and_retrieve():
    memory = MemoryService()
    memory.add("The sky is blue", {"source": "test"})
    assert memory.retrieve("sky") == [
        {"text": "The sky is blue", "metadata": {"source": "test"}}
    ]


def test_memory_service_metadata_filter():
    memory = MemoryService()
    memory.add("blue sky", {"Source": "Test"})
    memory.add("blue ocean", {"source": "other"})
    results = memory.retrieve("blue", metadata={"source": "test"})
    assert results == [{"text": "blue sky", "metadata": {"Source": "Test"}}]
    assert memory.retrieve("blue", metadata={"SOURCE": "TEST"}) == results
    assert memory.retrieve("blue", metadata={"source": "missing"}) == []


def test_memory_service_non_string_metadata():
    memory = MemoryService()
    memory.add("blue cube", {"count": 1})
    expected = [{"text": "blue cube", "metadata": {"count": 1}}]
    assert memory.retrieve("blue", metadata={"count": 1}) == expected
    assert memory.retrieve("blue", metadata={"count": "1"}) == expected


def test_memory_service_retrieve_returns_copy():
    memory = MemoryService()
    memory.add("original", {"source": "a"})
    retrieved = memory.retrieve("original")[0]
    retrieved["metadata"]["source"] = "changed"
    assert memory.memories[0]["metadata"]["source"] == "a"


def test_memory_service_limit_zero():
    memory = MemoryService()
    memory.add("original")
    assert memory.retrieve("original", limit=0) == []


def test_memory_service_empty_query():
    memory = MemoryService()
    memory.add("blue")
    assert memory.retrieve("") == []
    assert memory.retrieve("   ") == []

