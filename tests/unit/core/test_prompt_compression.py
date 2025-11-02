import os
from platform.observability import metrics
from src.ultimate_discord_intelligence_bot.services.prompt_engine import PromptEngine
from platform.core.settings import get_settings

def _enable_flag():
    os.environ['ENABLE_PROMPT_COMPRESSION'] = '1'
    get_settings.cache_clear()

def test_prompt_compression_basic_ratio(monkeypatch):
    _enable_flag()
    metrics.reset()
    pe = PromptEngine()
    original = 'Line 1\n\n\nLine 2\nLine 2\n' + 'A ' * 50
    optimised = pe.optimise(original)
    assert 'Line 2' in optimised
    assert optimised.count('Line 2') <= 2
    assert len(optimised) <= len(original)

def test_prompt_compression_disabled(monkeypatch):
    if 'ENABLE_PROMPT_COMPRESSION' in os.environ:
        del os.environ['ENABLE_PROMPT_COMPRESSION']
    get_settings.cache_clear()
    metrics.reset()
    pe = PromptEngine()
    original = 'Line 1\n\n\nLine 2'
    optimised = pe.optimise(original)
    assert optimised == original.strip()

def test_prompt_compression_enable_then_disable_regression(monkeypatch):
    """Ensure enabling then disabling restores original behavior.

    This guards against stale cached settings instances residing under an
    alternate import path (e.g. ``core.settings`` vs ``src.core.settings``)
    retaining a True flag after the env var is removed.
    """
    _enable_flag()
    metrics.reset()
    pe = PromptEngine()
    noisy = 'Line X\n\n\nLine Y\nLine Y'
    compressed = pe.optimise(noisy)
    assert compressed.count('Line Y') <= 2
    if 'ENABLE_PROMPT_COMPRESSION' in os.environ:
        del os.environ['ENABLE_PROMPT_COMPRESSION']
    get_settings.cache_clear()
    metrics.reset()
    restored = pe.optimise(noisy)
    assert restored == noisy.strip()