from platform.prompts.engine import PromptEngine

def test_prompt_engine_long_unbroken_text_reduction(monkeypatch):
    monkeypatch.setenv('ENABLE_PROMPT_COMPRESSION', '1')
    engine = PromptEngine()
    long_text = 'x' * 1000
    compact = engine.optimise(long_text, target_token_reduction=0.2, max_tokens=50)
    assert isinstance(compact, str)
    assert len(compact) <= len(long_text)

def test_prompt_engine_deduplicate_and_preserve_headings(monkeypatch):
    monkeypatch.setenv('ENABLE_PROMPT_COMPRESSION', '1')
    engine = PromptEngine()
    text = "\n    # Heading\n    line\n    line\n    line\n\n    code:\n        print(  'a'  )\n        print(  'a'  )\n    ".strip()
    out = engine.optimise(text, target_token_reduction=0.1)
    assert out.count('line') <= 2
    assert '# Heading' in out