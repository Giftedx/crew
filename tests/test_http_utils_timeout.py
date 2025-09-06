from __future__ import annotations

import importlib


def test_http_timeout_env_applied(monkeypatch):
    monkeypatch.setenv("HTTP_TIMEOUT", "42")
    from core import http_utils

    importlib.reload(http_utils)  # reload to apply env change to REQUEST_TIMEOUT_SECONDS

    captured = {}

    def fake_get(url, **kwargs):
        captured.update(kwargs)
        class R:
            status_code = 200
            text = "ok"
            def json(self):
                return {}
            def raise_for_status(self):
                return None
            def iter_content(self, chunk_size=8192):
                yield b""
        return R()

    # Use resilient_get directly
    resp = http_utils.resilient_get("https://example.com", request_fn=fake_get)
    assert resp.status_code == 200
    assert int(captured.get("timeout", 0)) == 42

