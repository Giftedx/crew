import logging
import pytest
from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline
from platform.core.step_result import StepResult

class DummySpan:

    def set_attribute(self, *_args, **_kwargs):
        return None

class DummyCtx:

    def __init__(self):
        self.span = DummySpan()

class DummyTranscription:

    def __init__(self, text: str):
        self.filtered_transcript = text

@pytest.mark.asyncio
async def test_governance_phase_blocks_on_red_lines(monkeypatch):
    monkeypatch.setenv('ENABLE_CONTENT_SAFETY_CLASSIFICATION', '1')
    monkeypatch.setenv('ENABLE_RED_LINE_GUARDS', '1')
    pipeline = object.__new__(ContentPipeline)
    pipeline.logger = logging.getLogger('test')

    async def fake_execute_step(_step, _func, _payload):
        return StepResult.ok(categories=['violence'], action='block', confidence=0.95, details={})
    pipeline._execute_step = fake_execute_step
    ctx = DummyCtx()
    tb = DummyTranscription('This mentions a weapon and potential attack')
    result, blocked = await pipeline._governance_phase(ctx, tb, routing_result=None)
    assert result.success is True
    assert blocked is True
    data = result.data
    if 'result' in data and isinstance(data['result'], dict):
        data = data['result']
    assert data.get('action') == 'block'
    assert 'violence' in (data.get('categories') or [])