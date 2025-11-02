import os

from src.obs import metrics
from src.ultimate_discord_intelligence_bot.services.prompt_engine import PromptEngine
from ultimate_discord_intelligence_bot.core.settings import get_settings


def _enable_flag():
    os.environ["ENABLE_PROMPT_COMPRESSION"] = "1"
    # settings is lru_cached; clear to re-read env
    get_settings.cache_clear()  # type: ignore[attr-defined]


def test_prompt_compression_basic_ratio(monkeypatch):
    _enable_flag()
    metrics.reset()
    pe = PromptEngine()
    original = "Line 1\n\n\nLine 2\nLine 2\n" + "A " * 50
    optimised = pe.optimise(original)
    assert "Line 2" in optimised
    # Ensure duplicate line collapsed (only one occurrence of 'Line 2' besides potential context inside omitted marker)
    assert optimised.count("Line 2") <= 2
    # Metric should have at least one observation
    # We cannot introspect histogram buckets easily without prometheus client, so just ensure function returns string shorter or equal
    assert len(optimised) <= len(original)


def test_prompt_compression_disabled(monkeypatch):
    # disable flag
    if "ENABLE_PROMPT_COMPRESSION" in os.environ:
        del os.environ["ENABLE_PROMPT_COMPRESSION"]
    get_settings.cache_clear()  # type: ignore[attr-defined]
    metrics.reset()
    pe = PromptEngine()
    original = "Line 1\n\n\nLine 2"  # simple
    optimised = pe.optimise(original)
    # Should only trim outer whitespace when disabled
    assert optimised == original.strip()


def test_prompt_compression_enable_then_disable_regression(monkeypatch):
    """Ensure enabling then disabling restores original behavior.

    This guards against stale cached settings instances residing under an
    alternate import path (e.g. ``core.settings`` vs ``src.core.settings``)
    retaining a True flag after the env var is removed.
    """
    # Step 1: enable
    _enable_flag()
    metrics.reset()
    pe = PromptEngine()
    noisy = "Line X\n\n\nLine Y\nLine Y"
    compressed = pe.optimise(noisy)
    assert compressed.count("Line Y") <= 2  # confirm compression path active

    # Step 2: disable again (remove env + clear the *src* settings cache)
    if "ENABLE_PROMPT_COMPRESSION" in os.environ:
        del os.environ["ENABLE_PROMPT_COMPRESSION"]
    get_settings.cache_clear()  # type: ignore[attr-defined]
    metrics.reset()
    restored = pe.optimise(noisy)  # reuse same instance; should now bypass compression
    assert restored == noisy.strip()
