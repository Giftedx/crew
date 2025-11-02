"""Tests for PromptEngine contextual prompts."""
from domains.memory.vector_store import MemoryService
from platform.prompts.engine import PromptEngine

def test_prompt_engine_injects_context_sources():
    mem = MemoryService()
    mem.add('Ethan greets the audience', {'source': 'video1', 'ts': 10})
    engine = PromptEngine(memory=mem)
    prompt = engine.build_with_context('Answer the question', 'Ethan', k=1)
    assert 'video1#10' in prompt
    assert 'Ethan greets the audience' in prompt