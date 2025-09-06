import importlib

MODULE_PATH = "ultimate_discord_intelligence_bot.settings"


def reload_settings(monkeypatch, **env):
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    return importlib.reload(importlib.import_module(MODULE_PATH))


def test_secure_qdrant_fallback_disabled(monkeypatch):
    # With flag unset and no env var, value should be empty. Disable dotenv load to avoid .env leakage.
    settings = reload_settings(
        monkeypatch,
        QDRANT_URL=None,
        CREW_ENABLE_SECURE_QDRANT_FALLBACK=None,
        CREW_DISABLE_DOTENV="1",
    )
    assert settings.QDRANT_URL == ""


def test_secure_qdrant_fallback_enabled(monkeypatch):
    # Use injection env var to simulate secure config fallback deterministically.
    monkeypatch.setenv("CREW_ENABLE_SECURE_QDRANT_FALLBACK", "1")
    monkeypatch.setenv("CREW_DISABLE_DOTENV", "1")
    monkeypatch.setenv("CREW_QDRANT_SECURE_TEST_URL", "https://secure.example")
    monkeypatch.delenv("QDRANT_URL", raising=False)

    settings = importlib.reload(importlib.import_module(MODULE_PATH))
    assert settings.QDRANT_URL == "https://secure.example"
