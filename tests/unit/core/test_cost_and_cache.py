from __future__ import annotations
import pytest
from core import alerts, learning_engine, reliability, router, token_meter
from discord import commands
from platform.cache.bounded_cache import BoundedLRUCache

def test_cost_guard_rejects_and_downshifts() -> None:
    token_meter.budget.max_per_request = 0.0001
    engine = learning_engine.LearningEngine()
    r = router.Router(engine)
    with pytest.raises(token_meter.BudgetError):
        r.preflight('hello', ['gpt-4'], expected_output_tokens=10)
    model = r.preflight('hello', ['gpt-4', 'gpt-3.5'], expected_output_tokens=10)
    assert model == 'gpt-3.5'

def test_llm_cache_hits() -> None:
    c = BoundedLRUCache(ttl=1, max_size=1)
    c.set('key1', 'value1')
    assert c.get('key1') == 'value1'
    c.set('key2', 'value2')
    assert c.get('key1') is None
    assert c.get('key2') == 'value2'

def test_retry_succeeds() -> None:
    attempts = {'n': 0}

    def flake():
        attempts['n'] += 1
        if attempts['n'] < 3:
            raise ValueError('fail')
        return 'ok'
    result = reliability.retry(flake, retries=3, backoff=0)
    assert result == 'ok'
    assert attempts['n'] == 3

def test_ops_status_includes_alerts() -> None:
    alerts.alerts.record('test')
    status = commands.ops_status(1.0, cache_hits=0, breaker_open=False, alerts=alerts.alerts.drain())
    assert status['alerts'] == ['test']