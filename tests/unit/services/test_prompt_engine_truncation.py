from __future__ import annotations
from platform.prompts.engine import PromptEngine

def test_emergency_truncation_minimal_tokens_enabled(monkeypatch):
    monkeypatch.setenv('ENABLE_PROMPT_COMPRESSION', '1')
    engine = PromptEngine()
    text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n' * 20
    out = engine.optimise(text, target_token_reduction=0.0, max_tokens=2)
    assert out in ('[truncated]', '')

def test_emergency_truncation_head_tail_marker(monkeypatch):
    monkeypatch.setenv('ENABLE_PROMPT_COMPRESSION', '1')
    engine = PromptEngine()
    lines = [f'line-{i}' for i in range(30)]
    text = '\n'.join(lines)
    out = engine.optimise(text, target_token_reduction=0.0, max_tokens=20)
    assert '...[omitted' in out or out.endswith('...')

def test_max_tokens_ignored_when_disabled(monkeypatch):
    monkeypatch.delenv('ENABLE_PROMPT_COMPRESSION', raising=False)
    monkeypatch.delenv('PROMPT_COMPRESSION_SOURCE', raising=False)
    engine = PromptEngine()
    text = 'a\n\n\n' + 'b ' * 1000
    out = engine.optimise(text, target_token_reduction=0.0, max_tokens=1)
    assert out == text.strip()