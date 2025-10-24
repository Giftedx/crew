from core import (
    eval_harness,
    flags,
    learning_engine,
    log_schema,
    prompt_engine,
    router,
    token_meter,
)


def test_prompt_engine_builds_prompt_with_context_and_tools():
    prompt = prompt_engine.build_prompt("Hello", context="world", tools=["search"])
    assert "You are a helpful assistant." in prompt
    assert "Context:\nworld" in prompt
    assert "Available tools:\nsearch" in prompt


def test_token_meter_estimates_cost():
    tc = token_meter.measure("hello world", "gpt-3.5")
    assert tc.tokens > 0
    assert tc.cost_usd > 0


def test_learning_engine_and_router():
    engine = learning_engine.LearningEngine()
    engine.register_domain("routing")
    r = router.Router(engine)
    choice = r.route("task", ["gpt-3.5", "gpt-4"], {"foo": "bar"})
    assert choice in {"gpt-3.5", "gpt-4"}
    engine.record("routing", {"foo": "bar"}, choice, reward=1.0)


def test_eval_harness_bakeoff():
    def cand_good():
        return {"cost_usd": 1.0, "latency_ms": 10}, {"quality": 1.0}

    def cand_bad():
        return {"cost_usd": 1.0, "latency_ms": 10}, {"quality": 0.0}

    res = eval_harness.bakeoff({"good": cand_good, "bad": cand_bad}, {})
    assert res["good"].reward > res["bad"].reward


def test_flags_enabled(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_FLAG", "true")
    assert flags.enabled("TEST_FLAG")
    assert not flags.enabled("OTHER_FLAG")


def test_log_schema_dataclasses():
    log = log_schema.LLMCallLog(
        prompt="hi",
        response="bye",
        model="gpt-3.5",
        provider="openai",
        tokens_prompt=1,
        tokens_completion=1,
        cost_usd=0.001,
        latency_ms=5.0,
    )
    assert log.model == "gpt-3.5"
