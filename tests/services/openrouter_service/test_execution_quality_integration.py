import pytest
import platform.llm.providers.openrouter as or_pkg
from platform.observability import metrics as _metrics
from platform.llm.providers.openrouter.context import prepare_route_state
from platform.llm.providers.openrouter.execution import execute_online
from platform.llm.providers.openrouter.service import OpenRouterService

class _FakeResponse:

    def __init__(self, status_code=200, json_obj=None, text=''):
        self.status_code = status_code
        self._json = json_obj or {}
        self.text = text

    def json(self):
        return self._json

@pytest.fixture(autouse=True)
def stub_metrics():
    """Stub required Prometheus metrics to no-op to avoid import/registration issues in tests."""

    class _DummyMetric:

        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            return None

        def observe(self, *args, **kwargs):
            return None

        def set(self, *args, **kwargs):
            return None
    needed = ['ROUTER_DECISIONS', 'ACTIVE_BANDIT_POLICY', 'LLM_MODEL_SELECTED', 'LLM_ESTIMATED_COST', 'LLM_LATENCY', 'SEMANTIC_CACHE_PREFETCH_USED', 'SEMANTIC_CACHE_PREFETCH_ISSUED', 'SEMANTIC_CACHE_SHADOW_HITS', 'SEMANTIC_CACHE_SHADOW_MISSES', 'CACHE_PROMOTIONS', 'SEMANTIC_CACHE_SIMILARITY', 'LLM_CACHE_HITS', 'LLM_CACHE_MISSES']
    stash = {}
    for name in needed:
        stash[name] = getattr(_metrics, name, None)
        setattr(_metrics, name, _DummyMetric())
    try:
        yield
    finally:
        for name, original in stash.items():
            if original is None:
                try:
                    delattr(_metrics, name)
                except Exception:
                    pass
            else:
                setattr(_metrics, name, original)

@pytest.fixture
def restore_resilient_post():
    original = getattr(or_pkg, 'resilient_post', None)
    yield original
    if original is not None:
        or_pkg.resilient_post = original
    elif hasattr(or_pkg, 'resilient_post'):
        del or_pkg.resilient_post

def test_quality_metadata_attached_on_success(restore_resilient_post):

    def _stub_resilient_post(url, json_payload=None, headers=None, timeout_seconds=None, **_):
        return _FakeResponse(200, {'choices': [{'message': {'content': 'Python is a high-level language.\n- Easy to read\n- Large ecosystem'}}]})
    or_pkg.resilient_post = _stub_resilient_post
    svc = OpenRouterService(api_key='sk-test')
    res = svc.route('Explain Python and list two benefits.', task_type='general', model='openai/gpt-4o-mini')
    assert res.get('status') == 'success'
    assert 'quality_assessment' in res, 'quality assessment should be attached to results'
    qa = res['quality_assessment']
    assert 0.0 <= qa['score'] <= 1.0
    assert isinstance(qa.get('signals'), dict)

def test_quality_min_tokens_provider_override(restore_resilient_post):

    def _stub_resilient_post(url, json_payload=None, headers=None, timeout_seconds=None, **_):
        return _FakeResponse(200, {'choices': [{'message': {'content': 'word ' * 10}}]})
    or_pkg.resilient_post = _stub_resilient_post
    svc = OpenRouterService(api_key='sk-test')
    res = svc.route('Provide a short list.', task_type='general', model='openai/gpt-4o-mini', provider_opts={'quality_min_tokens': 200})
    assert res.get('status') == 'success'
    qa = res.get('quality_assessment')
    assert qa is not None, 'quality assessment should be present'
    assert qa.get('min_tokens') == 200

def test_overflow_retry_via_execute_online_sets_quality_and_compression(restore_resilient_post):
    import time as _t
    call_counter = {'n': 0}

    def _stub_resilient_post(url, json_payload=None, headers=None, timeout_seconds=None, **_):
        call_counter['n'] += 1
        if call_counter['n'] == 1:
            return _FakeResponse(413, {'error': {'message': 'prompt is too long'}}, text='prompt is too long')
        return _FakeResponse(200, {'choices': [{'message': {'content': 'Here is a compressed and valid response after retry.'}}]})
    or_pkg.resilient_post = _stub_resilient_post
    svc = OpenRouterService(api_key='sk-test')

    def _simple_compress(text, **kwargs):
        shortened = (text or '')[:max(50, int(len(text) * 0.5))]
        return (shortened, {'final_tokens': len(shortened.split()), 'stages': []})
    svc.prompt_engine.optimise_with_metadata = _simple_compress
    state = prepare_route_state(svc, 'x' * 5000, task_type='general', model='openai/gpt-4o-mini', provider_opts=None)
    state.start_time = _t.perf_counter()
    res = execute_online(svc, state)
    assert res.get('status') == 'success'
    assert res.get('retry_reason') == 'overflow_detected'
    assert 'compression_info' in res and isinstance(res['compression_info'], dict)
    assert 'quality_assessment' in res