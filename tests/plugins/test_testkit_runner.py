from importlib import import_module

from ultimate_discord_intelligence_bot.plugins.testkit.runner import run


def test_example_plugin_passes():
    report = run("ultimate_discord_intelligence_bot.plugins.example_summarizer")
    assert all(r["passed"] for r in report["results"]), report


def test_forbidden_scorer_triggers_failure(monkeypatch):
    module = import_module("ultimate_discord_intelligence_bot.plugins.example_summarizer")

    def bad_run(adapters, text):  # pragma: no cover - exercised in test
        return "stubbed error"

    monkeypatch.setattr(module, "run", bad_run)
    report = run("ultimate_discord_intelligence_bot.plugins.example_summarizer")
    assert not all(r["passed"] for r in report["results"])
    assert any(r["reason"] == "forbidden failed" for r in report["results"])
