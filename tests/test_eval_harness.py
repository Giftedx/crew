import json
from pathlib import Path

from ultimate_discord_intelligence_bot.services.eval_harness import (
    score_must_include, score_must_link, score_forbidden,
    score_grounded, run_dataset, compare_to_baseline,
)


def test_scorers_basic(tmp_path):
    out = "This answer has a link http://example.com and nothing bad"
    expected = {
        "must_include": ["answer"],
        "must_link": ["http://example.com"],
        "forbidden": ["badword"],
    }
    record = {"input": {}, "expected": expected}
    assert score_must_include(out, expected) == 1.0
    assert score_must_link(out, expected) == 1.0
    assert score_forbidden(out, expected) == 1.0
    assert score_grounded(out, record) == 1.0


def test_run_and_baseline(tmp_path):
    dataset = tmp_path / "data.jsonl"
    dataset.write_text(json.dumps({
        "task": "analyze_claim",
        "input": {"query": "q"},
        "expected": {"must_include": ["no"]}
    }) + "\n")

    def runner(_input):
        return {"output": "no", "cost_usd": 0.0, "latency_ms": 0.0}

    result = run_dataset(dataset, runner)
    assert result.aggregates["quality"] == 1.0

    baseline_path = Path("benchmarks/baselines.yaml")
    original = baseline_path.read_text() if baseline_path.exists() else ""
    baseline_path.write_text("test:\n  quality: 1.0\n  cost_usd: 0.0\n  latency_ms: 0.0\n  lambda: 0.0\n  mu: 0.0\n")
    try:
        assert compare_to_baseline(result, "test", {"quality": 0.1, "cost_usd": 0.0, "latency_ms": 0.0})
    finally:
        if original:
            baseline_path.write_text(original)
