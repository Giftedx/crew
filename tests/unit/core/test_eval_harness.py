from __future__ import annotations

from pathlib import Path

import pytest

from eval import gates, loader, runner


def stub_model(task: str, case: dict):
    if task == "rag_qa":
        return "The sky is blue", {"cost_usd": 0.0, "latency_ms": 0}
    if task == "summarize":
        return "Paris is the capital", {"cost_usd": 0.0, "latency_ms": 0}
    if task == "classification":
        return case["expected"], {"cost_usd": 0.0, "latency_ms": 0}
    if task == "claimcheck":
        return case["expected_label"], {"cost_usd": 0.0, "latency_ms": 0}
    if task == "tool_tasks":
        import json

        return json.dumps(case["expected"]), {"cost_usd": 0.0, "latency_ms": 0}
    return "", {"cost_usd": 0.0, "latency_ms": 0}


def test_loader_and_runner(tmp_path: Path):
    data_dir = Path("datasets/golden/core/v1")
    cases = loader.load_cases(data_dir)
    assert "rag_qa" in cases and cases["rag_qa"][0]["id"] == "q1"

    _report = runner.run(data_dir, stub_model)
    assert _report["rag_qa"]["quality"] == 1.0


@pytest.mark.integration
def test_summary_json_structure():
    """Ensure the baseline summary.json conforms to expected schema."""
    with open("benchmarks/baselines/golden/core/v1/summary.json") as f:
        import json

        baseline = json.load(f)
    # Recompute report inside this test to avoid cross-test variable dependence
    data_dir = Path("datasets/golden/core/v1")
    report2 = runner.run(data_dir, stub_model)
    result = gates.compare(report2, baseline)
    assert result["pass"]
