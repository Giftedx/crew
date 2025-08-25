import importlib
from pathlib import Path

import pytest

MODULE_PATH = "ultimate_discord_intelligence_bot___complete_social_media_analysis_fact_checking_system.settings"


def reload_settings(monkeypatch, **env):
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    return importlib.reload(importlib.import_module(MODULE_PATH))


def test_base_dir_env_override(monkeypatch):
    tmp = Path("/tmp/crewtest")
    settings = reload_settings(monkeypatch, CREWAI_BASE_DIR=str(tmp))
    assert settings.BASE_DIR == tmp


def test_base_dir_default(monkeypatch):
    settings = reload_settings(monkeypatch, CREWAI_BASE_DIR=None)
    assert settings.BASE_DIR.name == "CrewAI_Content_System"


def test_path_envs_expand_user(monkeypatch, tmp_path):
    env_home = tmp_path / "home"
    downloads = "~/downloads"
    settings = reload_settings(
        monkeypatch,
        HOME=str(env_home),
        CREWAI_BASE_DIR=str(tmp_path / "base"),
        CREWAI_DOWNLOADS_DIR=downloads,
    )
    assert settings.DOWNLOADS_DIR == env_home / "downloads"
