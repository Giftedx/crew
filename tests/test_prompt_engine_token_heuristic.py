import importlib

import pytest


def _get_module():
    return importlib.import_module("ultimate_discord_intelligence_bot.services.prompt_engine")


def test_short_unbroken_text_no_heuristic(monkeypatch):
    pe_mod = _get_module()
    # Force fallback path by disabling optional tokenizers
    monkeypatch.setattr(pe_mod, "tiktoken", None, raising=False)
    monkeypatch.setattr(pe_mod, "AutoTokenizer", None, raising=False)

    engine = pe_mod.PromptEngine()
    text = "x" * 100  # below heuristic threshold (200)
    tokens = engine.count_tokens(text)

    # With whitespace fallback, a single unbroken word counts as 1 token
    assert tokens == 1


def test_long_unbroken_text_applies_heuristic(monkeypatch):
    pe_mod = _get_module()
    # Force fallback path by disabling optional tokenizers
    monkeypatch.setattr(pe_mod, "tiktoken", None, raising=False)
    monkeypatch.setattr(pe_mod, "AutoTokenizer", None, raising=False)

    engine = pe_mod.PromptEngine()
    text = "x" * 400  # above heuristic threshold; approx tokens ~ len // 4
    tokens = engine.count_tokens(text)

    assert tokens == 100  # 400 // 4


@pytest.mark.parametrize("words,count", [(1, 1), (5, 5), (10, 10)])
def test_space_separated_counts_with_fallback(monkeypatch, words, count):
    pe_mod = _get_module()
    # Force fallback path by disabling optional tokenizers
    monkeypatch.setattr(pe_mod, "tiktoken", None, raising=False)
    monkeypatch.setattr(pe_mod, "AutoTokenizer", None, raising=False)

    engine = pe_mod.PromptEngine()
    text = " ".join(["word"] * words)
    tokens = engine.count_tokens(text)

    assert tokens == count
