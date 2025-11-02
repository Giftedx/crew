import importlib
import pytest
from platform.core.settings import get_settings
from platform.prompts.engine import PromptEngine

@pytest.fixture(autouse=True)
def _reset_env(monkeypatch):
    monkeypatch.delenv('ENABLE_PROMPT_COMPRESSION', raising=False)
    monkeypatch.delenv('PROMPT_COMPRESSION_SOURCE', raising=False)
    monkeypatch.delenv('ENABLE_LLMLINGUA', raising=False)
    monkeypatch.delenv('ENABLE_LLMLINGUA_SHADOW', raising=False)
    yield

def test_optimise_with_metadata_disabled(monkeypatch):
    engine = PromptEngine()
    text, meta = engine.optimise_with_metadata(' Hello World ')
    assert text == 'Hello World'
    assert meta['enabled'] is False
    assert meta['final_tokens'] == meta['original_tokens']

def test_optimise_with_metadata_basic_stage(monkeypatch):
    monkeypatch.setenv('ENABLE_PROMPT_COMPRESSION', '1')
    settings = get_settings()
    monkeypatch.setattr(settings, 'llmlingua_min_tokens', 10, raising=False)
    monkeypatch.setattr(settings, 'prompt_compression_default_target', 0.0, raising=False)
    engine = PromptEngine()
    text, meta = engine.optimise_with_metadata('line1\n\n\nline2', model='gpt-3.5-turbo')
    assert meta['enabled'] is True
    assert any((stage['stage'] == 'basic' for stage in meta['stages']))
    assert text.count('\n\n') <= 1

def test_llmlingua_active_applies(monkeypatch):
    monkeypatch.setenv('ENABLE_PROMPT_COMPRESSION', '1')
    monkeypatch.setenv('ENABLE_LLMLINGUA', '1')
    settings = get_settings()
    monkeypatch.setattr(settings, 'llmlingua_min_tokens', 1, raising=False)
    monkeypatch.setattr(settings, 'prompt_compression_default_target', 0.0, raising=False)
    calls = {}

    def _stub(prompt, **kwargs):
        calls['kwargs'] = kwargs
        return ('compressed-output', {'applied': True, 'kwargs': kwargs})
    module = importlib.import_module('ultimate_discord_intelligence_bot.services.prompt_engine')
    monkeypatch.setattr(module, 'compress_prompt_with_details', _stub)
    engine = PromptEngine()
    text, meta = engine.optimise_with_metadata('A' * 50, model='gpt-3.5-turbo')
    assert text == 'compressed-output'
    assert meta['llmlingua']['mode'] == 'active'
    assert meta['llmlingua']['applied'] is True
    assert 'target_tokens' in meta['llmlingua']
    assert calls['kwargs']['enabled'] is True

def test_llmlingua_shadow_mode_retains_original(monkeypatch):
    monkeypatch.setenv('ENABLE_PROMPT_COMPRESSION', '1')
    monkeypatch.setenv('ENABLE_LLMLINGUA_SHADOW', '1')
    settings = get_settings()
    monkeypatch.setattr(settings, 'llmlingua_min_tokens', 1, raising=False)
    monkeypatch.setattr(settings, 'prompt_compression_default_target', 0.0, raising=False)
    monkeypatch.setattr(settings, 'enable_llmlingua', False, raising=False)
    module = importlib.import_module('ultimate_discord_intelligence_bot.services.prompt_engine')

    def _shadow(prompt, **kwargs):
        return ('shadow-output', {'applied': True, 'kwargs': kwargs})
    monkeypatch.setattr(module, 'compress_prompt_with_details', _shadow)
    engine = PromptEngine()
    text, meta = engine.optimise_with_metadata('B' * 50, model='gpt-3.5-turbo')
    assert text != 'shadow-output'
    assert meta['llmlingua']['mode'] == 'shadow'
    assert meta['llmlingua']['details']['applied'] is True
    assert meta['llmlingua'].get('shadow_after_tokens') is not None

def test_force_enable_overrides_env(monkeypatch):
    engine = PromptEngine()
    text, meta = engine.optimise_with_metadata('row1\n\n\nrow2', force_enable=True)
    assert meta['enabled'] is True
    assert meta['forced'] is True
    assert '\n\n\n' not in text