from ultimate_discord_intelligence_bot.plugins.testkit.runner import run


def test_example_plugin_passes():
    report = run("ultimate_discord_intelligence_bot.plugins.example_summarizer")
    assert all(r["passed"] for r in report["results"]), report
