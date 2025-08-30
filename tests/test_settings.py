import importlib
from pathlib import Path

MODULE_PATH = "ultimate_discord_intelligence_bot.settings"


def reload_settings(monkeypatch, **env):
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    return importlib.reload(importlib.import_module(MODULE_PATH))


def test_base_dir_env_override(monkeypatch):
    tmp = Path("/tmp/crewtest")  # noqa: S108 - controlled temporary directory for test isolation
    settings = reload_settings(monkeypatch, CREWAI_BASE_DIR=str(tmp))
    assert tmp == settings.BASE_DIR


def test_base_dir_default(monkeypatch):
    settings = reload_settings(monkeypatch, CREWAI_BASE_DIR=None)
    assert settings.BASE_DIR.name == "crew_data"


def test_path_envs_expand_user(monkeypatch, tmp_path):
    env_home = tmp_path / "home"
    downloads = "~/downloads"
    settings = reload_settings(
        monkeypatch,
        HOME=str(env_home),
        CREWAI_BASE_DIR=str(tmp_path / "base"),
        CREWAI_DOWNLOADS_DIR=downloads,
    )
    assert env_home / "downloads" == settings.DOWNLOADS_DIR


def test_qdrant_url(monkeypatch):
    settings = reload_settings(monkeypatch, QDRANT_URL="http://localhost:6333")
    assert settings.QDRANT_URL == "http://localhost:6333"

    settings = reload_settings(monkeypatch, QDRANT_URL=None)
    assert settings.QDRANT_URL == ""


def test_private_webhook(monkeypatch):
    url = "https://discord.com/api/webhooks/test"
    settings = reload_settings(monkeypatch, DISCORD_PRIVATE_WEBHOOK=url)
    assert url == settings.DISCORD_PRIVATE_WEBHOOK
