from __future__ import annotations

from core.secure_config import reload_config
from fastapi.testclient import TestClient
from server.app import create_app


def test_alert_adapter_posts_to_discord(monkeypatch):
    monkeypatch.setenv("DISCORD_ALERT_WEBHOOK", "https://discord.com/api/webhooks/1/abc")
    _config = None  # Reset the cached config
    reload_config()
    app = create_app()
    client = TestClient(app)
    captured = {}

    def fake_post(url, json_payload=None, headers=None, timeout_seconds=None, **_):
        captured["url"] = url
        captured["json"] = json_payload
        class R:
            status_code = 204
            text = ""
        return R()

    import ops.alert_adapter as adapter

    monkeypatch.setattr(adapter, "resilient_post", fake_post)

    payload = {
        "status": "firing",
        "alerts": [
            {
                "labels": {"alertname": "LLMLatencyP95High", "tenant": "default", "workspace": "main", "severity": "warning"},
                "annotations": {"summary": "LLM latency high", "description": "p95 > 2.5s"},
            }
        ],
    }
    res = client.post("/ops/alerts/alert", json=payload)
    assert res.status_code == 200
    assert captured["url"].startswith("https://discord.com/api/webhooks/")
    assert "LLM latency high" in captured["json"]["content"]

