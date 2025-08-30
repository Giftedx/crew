from memory.qdrant_provider import _DummyClient, get_qdrant_client


def test_dummy_qdrant_fallback_memory_url(monkeypatch):
    # Force settings.qdrant_url to ':memory:'
    from core import settings as settings_mod

    class DummySettings:
        qdrant_url = ":memory:"
        qdrant_api_key = ""
        qdrant_prefer_grpc = False
        qdrant_grpc_port = None

    def fake_get_settings():
        return DummySettings()

    monkeypatch.setattr(settings_mod, "get_settings", fake_get_settings)
    client = get_qdrant_client()  # lru_cache will cache dummy
    assert isinstance(client, _DummyClient)


def test_dummy_qdrant_fallback_empty_url(monkeypatch):
    from core import settings as settings_mod

    class DummySettings2:
        qdrant_url = "  "  # blank triggers fallback
        qdrant_api_key = ""
        qdrant_prefer_grpc = False
        qdrant_grpc_port = None

    monkeypatch.setattr(settings_mod, "get_settings", lambda: DummySettings2())
    # Need to clear cache to re-evaluate settings
    get_qdrant_client.cache_clear()  # lru_cache attribute present; mypy sees attribute
    client = get_qdrant_client()
    assert isinstance(client, _DummyClient)
