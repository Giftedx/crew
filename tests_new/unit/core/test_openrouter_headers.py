from __future__ import annotations


def test_openrouter_includes_recommended_headers(monkeypatch):
    # Configure env for settings
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("OPENROUTER_REFERER", "https://example.com")
    monkeypatch.setenv("OPENROUTER_TITLE", "My Bot")

    # Reload configuration to pick up environment changes
    from ultimate_discord_intelligence_bot.core.secure_config import reload_config

    reload_config()

    # Clear settings cache to pick up new environment variables
    from ultimate_discord_intelligence_bot.core.settings import get_settings

    get_settings.cache_clear()

    # Import module under test after env is set
    import ultimate_discord_intelligence_bot.services.openrouter_service as svc_mod

    captured = {}

    class FakeResp:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "ok"}}]}

    def fake_post(url, headers=None, json_payload=None, timeout_seconds=None):
        captured["headers"] = headers
        return FakeResp()

    # Patch resilient_post used inside the module
    monkeypatch.setattr(svc_mod, "resilient_post", fake_post)
    # Disable retries path for simplicity
    monkeypatch.setattr(svc_mod, "is_retry_enabled", lambda: False)

    service = svc_mod.OpenRouterService(api_key="test-api-key")
    res = service.route("hi", task_type="general")
    assert res["status"] == "success"

    headers = captured["headers"]
    assert headers["Authorization"].startswith("Bearer ")
    assert headers.get("HTTP-Referer") == "https://example.com"
    assert headers.get("Referer") == "https://example.com"
    assert headers.get("X-Title") == "My Bot"
