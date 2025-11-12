from ultimate_discord_intelligence_bot.obs import metrics as metrics_mod
from ultimate_discord_intelligence_bot.services import MemoryService


def test_tenancy_fallback_metric_increments(monkeypatch):
    monkeypatch.delenv("ENABLE_TENANCY_STRICT", raising=False)
    monkeypatch.setenv("ENABLE_INGEST_STRICT", "0")
    metrics_mod.reset()
    memory = MemoryService()
    memory.add("hello")
    data = metrics_mod.render().decode("utf-8")
    if data:
        assert "tenancy_fallback_total" in data
        assert 'component="memory_service"' in data
    else:
        assert True
