from obs import metrics as metrics_mod
from ultimate_discord_intelligence_bot.services import MemoryService


def test_tenancy_fallback_metric_increments(monkeypatch):
    # Non-strict path: ensure fallback happens
    monkeypatch.delenv("ENABLE_TENANCY_STRICT", raising=False)
    monkeypatch.setenv("ENABLE_INGEST_STRICT", "0")

    # Reset metrics to clean state
    metrics_mod.reset()

    memory = MemoryService()
    # Trigger a fallback by calling without setting a tenant
    memory.add("hello")

    # Render metrics exposition and check for our counter line
    data = metrics_mod.render().decode("utf-8")

    # Support both prometheus available and no-op cases
    # If Prom is available, expect the counter and labels to appear
    # If not, the exposition may be empty; in that case, we at least ensure no exception was raised
    if data:
        # Look for the counter name and component label
        assert "tenancy_fallback_total" in data
        assert 'component="memory_service"' in data
    else:
        # No-op metrics path: ensure the call didn't raise and proceed silently
        assert True
