"""Tests for PromptEngine contextual prompts."""

from ultimate_discord_intelligence_bot.services.memory_service import MemoryService
from ultimate_discord_intelligence_bot.services.prompt_engine import PromptEngine


def test_prompt_engine_injects_context_sources():
    mem = MemoryService()
    mem.add("Ethan greets the audience", {"source": "video1", "ts": 10})
    engine = PromptEngine(memory=mem)
    prompt = engine.build_with_context("Answer the question", "Ethan", k=1)
    assert "video1#10" in prompt
    assert "Ethan greets the audience" in prompt
