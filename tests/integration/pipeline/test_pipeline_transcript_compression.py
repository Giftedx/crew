import logging
from ultimate_discord_intelligence_bot.pipeline_components.base import PipelineBase
from platform.prompts.engine import PromptEngine

def _make_pipeline_stub(**attrs):
    stub = object.__new__(PipelineBase)
    stub.logger = logging.getLogger('PipelineBaseTest')
    for key, value in attrs.items():
        setattr(stub, key, value)
    return stub

def test_maybe_compress_transcript_disabled():
    pipeline = _make_pipeline_stub(prompt_engine=PromptEngine(), _transcript_compression_enabled=False)
    text, meta = PipelineBase._maybe_compress_transcript(pipeline, 'plain text')
    assert meta is None
    assert text == 'plain text'

def test_maybe_compress_transcript_applies_basic_compression():
    pipeline = _make_pipeline_stub(prompt_engine=PromptEngine(), _transcript_compression_enabled=True, _transcript_compression_min_tokens=1, _transcript_compression_target_ratio=0.0, _transcript_compression_max_tokens=None)
    text, meta = PipelineBase._maybe_compress_transcript(pipeline, 'row1\n\n\nrow2')
    assert meta is not None
    assert meta['enabled'] is True
    assert meta['compressed'] is True
    assert '\n\n\n' not in text