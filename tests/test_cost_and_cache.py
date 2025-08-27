from __future__ import annotations

import time
import pytest

from core import cache, router, token_meter, learning_engine
from core import reliability


def test_cost_guard_rejects_and_downshifts() -> None:
    token_meter.budget.max_per_request = 0.0001
    engine = learning_engine.LearningEngine()
    r = router.Router(engine)
    with pytest.raises(token_meter.BudgetError):
        r.preflight("hello", ["gpt-4"], expected_output_tokens=10)
    model = r.preflight("hello", ["gpt-4", "gpt-3.5"], expected_output_tokens=10)
    assert model == "gpt-3.5"


def test_llm_cache_hits() -> None:
    c = cache.LLMCache(ttl=1)
    c.set("key", "value")
    assert c.get("key") == "value"
    time.sleep(1.1)
    assert c.get("key") is None


def test_retry_succeeds() -> None:
    attempts = {"n": 0}

    def flake():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise ValueError("fail")
        return "ok"

    result = reliability.retry(flake, retries=3, backoff=0)
    assert result == "ok"
    assert attempts["n"] == 3
