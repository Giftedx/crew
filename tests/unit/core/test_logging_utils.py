from ultimate_discord_intelligence_bot.services import AnalyticsStore, OpenRouterService


def test_analytics_store_logs_llm_calls(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    db = tmp_path / "analytics.db"
    store = AnalyticsStore(db_path=str(db))
    router = OpenRouterService(logger=store)
    router.route("hi", task_type="analysis")
    rows = list(store.fetch_llm_calls())
    assert rows and rows[0][0] == "analysis"
    store.close()
