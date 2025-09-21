from ultimate_discord_intelligence_bot.services.prompt_engine import PromptEngine


def test_prompt_engine_long_unbroken_text_reduction(monkeypatch):
    monkeypatch.setenv("ENABLE_PROMPT_COMPRESSION", "1")
    engine = PromptEngine()
    long_text = "x" * 1000  # no spaces
    # With optimise called, we expect some reduction via emergency trimming if max_tokens given
    compact = engine.optimise(long_text, target_token_reduction=0.2, max_tokens=50)
    assert isinstance(compact, str)
    assert len(compact) <= len(long_text)


def test_prompt_engine_deduplicate_and_preserve_headings(monkeypatch):
    monkeypatch.setenv("ENABLE_PROMPT_COMPRESSION", "1")
    engine = PromptEngine()
    text = """
    # Heading
    line
    line
    line

    code:
        print(  'a'  )
        print(  'a'  )
    """.strip()
    out = engine.optimise(text, target_token_reduction=0.1)
    assert out.count("line") <= 2  # deduped consecutive lines
    assert "# Heading" in out
