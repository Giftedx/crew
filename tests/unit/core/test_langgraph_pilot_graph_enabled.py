import pytest
from graphs.langgraph_pilot import run_ingest_analysis_pilot
from platform.observability import metrics

def test_langgraph_pilot_graph_enabled_happy_path(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('ENABLE_LANGGRAPH_PILOT', '1')
    metrics.reset()
    call_order: list[str] = []

    def _ingest(job: dict):
        call_order.append('ingest')
        return {'chunks': ['c1', 'c2'], 'ns': 't:w:ingest'}

    def _segment(ctx: dict):
        call_order.append('segment')
        assert 'chunks' in ctx and isinstance(ctx['chunks'], list)
        return {'segments': [s + ':seg' for s in ctx['chunks']]}

    def _embed(ctx: dict):
        call_order.append('embed')
        assert 'segments' in ctx
        return {'embeddings': [hash(s) % 1000 for s in ctx['segments']]}

    def _analyze(ctx: dict):
        call_order.append('analyze')
        assert ctx.get('embeddings')
        return {'analysis': {'count': len(ctx['embeddings'])}}
    out = run_ingest_analysis_pilot({'tenant': 't', 'workspace': 'w'}, _ingest, _analyze, segment_fn=_segment, embed_fn=_embed)
    assert out['ingest']['ns'] == 't:w:ingest'
    assert out['segment']['segments'][0].endswith(':seg')
    assert out['analysis']['analysis']['count'] == 2
    assert call_order == ['ingest', 'segment', 'embed', 'analyze']
    rendered = metrics.render().decode('utf-8') if metrics.PROMETHEUS_AVAILABLE else ''
    metric_names = 'pipeline_steps_completed_total' in rendered and 'step="ingest"' in rendered and ('step="embed"' in rendered) and ('step="langgraph_pilot"' in rendered)
    assert metric_names or not metrics.PROMETHEUS_AVAILABLE