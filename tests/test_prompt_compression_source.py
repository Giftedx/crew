from __future__ import annotations

import pytest


def _make_settings(enabled: bool):
    class _S:
        enable_prompt_compression = enabled
        enable_prompt_compression_flag = enabled
        prompt_compression_max_repeated_blank_lines = 1

    return _S()


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch):
    # Ensure a clean slate for each test
    for key in [
        "ENABLE_PROMPT_COMPRESSION",
        "PROMPT_COMPRESSION_SOURCE",
    ]:
        monkeypatch.delenv(key, raising=False)
    yield


def test_default_env_policy_ignores_settings_when_env_absent(monkeypatch: pytest.MonkeyPatch):
    # Import within test to ensure we patch the symbol used by the module
    from ultimate_discord_intelligence_bot.services import prompt_engine as pe

    # Default policy: PROMPT_COMPRESSION_SOURCE not set (treated as 'env')
    monkeypatch.delenv("PROMPT_COMPRESSION_SOURCE", raising=False)
    monkeypatch.delenv("ENABLE_PROMPT_COMPRESSION", raising=False)

    # Settings indicate enabled, but env is absent -> should be ignored under default policy
    monkeypatch.setattr(pe, "get_settings", lambda: _make_settings(True))

    engine = pe.PromptEngine()
    original = "line1\n\n\nline2"
    out = engine.optimise(original, target_token_reduction=0.0)
    # Since compression is effectively disabled, output should be original stripped
    assert out == original.strip()


def test_settings_policy_honors_settings(monkeypatch: pytest.MonkeyPatch):
    from ultimate_discord_intelligence_bot.services import prompt_engine as pe

    monkeypatch.setenv("PROMPT_COMPRESSION_SOURCE", "settings")
    monkeypatch.delenv("ENABLE_PROMPT_COMPRESSION", raising=False)
    monkeypatch.setattr(pe, "get_settings", lambda: _make_settings(True))

    engine = pe.PromptEngine()
    original = "line1\n\n\nline2"
    out = engine.optimise(original, target_token_reduction=0.0)
    # Compression enabled: basic blank-line collapse should occur
    assert out != original.strip()
    assert out == "line1\n\nline2"


def test_both_policy_env_or_settings(monkeypatch: pytest.MonkeyPatch):
    from ultimate_discord_intelligence_bot.services import prompt_engine as pe

    # Case 1: settings enabled, env absent -> enabled
    monkeypatch.setenv("PROMPT_COMPRESSION_SOURCE", "both")
    monkeypatch.delenv("ENABLE_PROMPT_COMPRESSION", raising=False)
    monkeypatch.setattr(pe, "get_settings", lambda: _make_settings(True))

    engine = pe.PromptEngine()
    original = "a\n\n\nb"
    out = engine.optimise(original)
    assert out == "a\n\nb"

    # Case 2: settings disabled, env enabled -> enabled
    monkeypatch.setattr(pe, "get_settings", lambda: _make_settings(False))
    monkeypatch.setenv("ENABLE_PROMPT_COMPRESSION", "1")
    out2 = engine.optimise(original)
    assert out2 == "a\n\nb"

    # Case 3: both disabled -> disabled
    monkeypatch.setenv("ENABLE_PROMPT_COMPRESSION", "0")
    monkeypatch.setattr(pe, "get_settings", lambda: _make_settings(False))
    out3 = engine.optimise(original)
    assert out3 == original.strip()


def test_env_policy_env_present_false_but_settings_true(monkeypatch: pytest.MonkeyPatch):
    from ultimate_discord_intelligence_bot.services import prompt_engine as pe

    # Default policy ('env'): when env var is present but false, settings can still enable
    monkeypatch.delenv("PROMPT_COMPRESSION_SOURCE", raising=False)
    monkeypatch.setenv("ENABLE_PROMPT_COMPRESSION", "0")  # present but falsy
    monkeypatch.setattr(pe, "get_settings", lambda: _make_settings(True))

    engine = pe.PromptEngine()
    original = "x\n\n\ny"
    out = engine.optimise(original)
    # env_present True + settings_enabled True -> enabled per default policy
    assert out == "x\n\ny"
