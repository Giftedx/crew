import importlib
from pathlib import Path


MODULE_PATH = "ultimate_discord_intelligence_bot.settings"


def reload_settings():
    return importlib.reload(importlib.import_module(MODULE_PATH))


def test_dotenv_not_reloaded_after_first_import(monkeypatch, tmp_path):
    """If the settings module was already imported before a .env appears, it should NOT load it on reload.

    Rationale: We guarantee .env is loaded only once at initial process import time to make test
    mutation of os.environ deterministic. This test creates a .env AFTER initial import and ensures
    the sentinel prevents late injection of variables.
    """
    # Ensure variable absent
    monkeypatch.delenv("QDRANT_URL", raising=False)
    monkeypatch.delenv("CREW_DISABLE_DOTENV", raising=False)
    first = reload_settings()
    assert first.QDRANT_URL == ""  # starts empty

    # Now create a .env containing a value that would have been picked up if load_dotenv executed again
    repo_root = Path(__file__).resolve().parents[1]
    dotenv_path = repo_root / ".env"
    dotenv_path.write_text("QDRANT_URL=http://from-dotenv\n")

    second = reload_settings()
    # Should still be empty because .env is not re-loaded after first import
    assert second.QDRANT_URL == ""

    dotenv_path.unlink(missing_ok=True)
