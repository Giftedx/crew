import json

from ultimate_discord_intelligence_bot.services.evaluation_harness import (
    EvaluationHarness,
)


def test_evaluation_harness_logs_results(tmp_path, monkeypatch):
    log_file = tmp_path / "log.jsonl"
    harness = EvaluationHarness()
    harness.log_path = str(log_file)

    def fake_route(prompt, task_type="general", model=None):
        return {
            "status": "success",
            "model": model,
            "response": prompt.upper(),
            "tokens": len(prompt.split()),
        }

    monkeypatch.setattr(harness.router, "route", fake_route)
    results = harness.run("hello world", models=["a", "b"])
    assert len(results) == 2
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["model"] == "a"
    assert first["tokens"] == 2
    assert "latency" in first
