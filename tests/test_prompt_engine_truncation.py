from __future__ import annotations

from ultimate_discord_intelligence_bot.services.prompt_engine import PromptEngine


def test_emergency_truncation_minimal_tokens_enabled(monkeypatch):
    # Enable compression so optimise applies max_tokens logic
    monkeypatch.setenv("ENABLE_PROMPT_COMPRESSION", "1")

    engine = PromptEngine()

    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n" * 20
    # Force a very small token budget to exercise minimal return behavior
    out = engine.optimise(text, target_token_reduction=0.0, max_tokens=2)
    assert out in ("[truncated]", "")  # per implementation, <=2 tokens returns minimal


def test_emergency_truncation_head_tail_marker(monkeypatch):
    monkeypatch.setenv("ENABLE_PROMPT_COMPRESSION", "1")

    engine = PromptEngine()
    # Construct 30 lines to trigger head/tail truncation path
    lines = [f"line-{i}" for i in range(30)]
    text = "\n".join(lines)

    # Set a max_tokens lower than original token count (~30) to force truncation
    out = engine.optimise(text, target_token_reduction=0.0, max_tokens=20)
    # Expect the omission marker to appear in emergency truncation path
    assert "...[omitted" in out or out.endswith("...")


def test_max_tokens_ignored_when_disabled(monkeypatch):
    # Default policy with env absent => disabled
    monkeypatch.delenv("ENABLE_PROMPT_COMPRESSION", raising=False)
    monkeypatch.delenv("PROMPT_COMPRESSION_SOURCE", raising=False)

    engine = PromptEngine()
    text = "a\n\n\n" + ("b " * 1000)
    out = engine.optimise(text, target_token_reduction=0.0, max_tokens=1)
    # When disabled, optimise returns stripped original without truncation
    assert out == text.strip()
