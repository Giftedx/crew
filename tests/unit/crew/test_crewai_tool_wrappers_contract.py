from __future__ import annotations
from ultimate_discord_intelligence_bot.crewai_tool_wrappers import CrewAIToolWrapper, DiscordPostToolWrapper, MCPCallToolWrapper, PipelineToolWrapper
from platform.core.step_result import StepResult

class _DummyTool:

    def run(self, **_kwargs):
        raise TypeError('missing required arg: text')

class _DummyDiscord:

    def _run(self, *_args, **_kwargs):
        return {'posted': True}

class _DummyMCP:

    def run(self, **_kwargs):
        raise RuntimeError('mcp failure')

class _DummyPipeline:

    def run(self, **_kwargs):
        raise RuntimeError('pipeline unavailable')

def test_crewai_tool_wrapper_returns_step_result_on_type_error() -> None:
    wrapper = CrewAIToolWrapper(_DummyTool())
    res = wrapper._run()
    assert isinstance(res, StepResult)
    assert not res.success
    assert 'missing required arg' in (res.error or '')

def test_discord_post_wrapper_returns_ok_result() -> None:
    wrapper = DiscordPostToolWrapper(_DummyDiscord)
    res = wrapper._run(message={'content': 'hello'})
    assert isinstance(res, StepResult)
    assert res.success

def test_mcp_wrapper_returns_fail_on_exception() -> None:
    wrapper = MCPCallToolWrapper(_DummyMCP())
    res = wrapper._run(namespace='obs', name='ping', params={})
    assert isinstance(res, StepResult)
    assert not res.success
    assert 'mcp' in (res.error or '').lower()

def test_pipeline_wrapper_returns_fail_on_exception() -> None:
    wrapper = PipelineToolWrapper(_DummyPipeline())
    res = wrapper._run(url='https://example.com', quality='720p')
    assert isinstance(res, StepResult)
    assert not res.success
    assert 'failed' in (res.error or '').lower()