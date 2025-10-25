from unittest.mock import MagicMock

from ultimate_discord_intelligence_bot.core.http_utils import (
    resilient_get,
    resilient_post,
)


def test_resilient_post_normal():
    captured = {}

    def fake(url, json=None, headers=None, files=None, timeout=None):
        captured["json"] = json
        r = MagicMock()
        r.status_code = 204
        r.text = ""
        return r

    resp = resilient_post("https://example.com", json_payload={"a": 1}, request_fn=fake)
    assert resp.status_code == 204
    assert captured["json"] == {"a": 1}


def test_resilient_post_legacy_timeout_fallback():
    calls = {"attempts": 0}

    def legacy(url, json=None, headers=None, files=None):  # missing timeout
        calls["attempts"] += 1
        r = MagicMock()
        r.status_code = 204
        r.text = ""
        return r

    resp = resilient_post("https://example.com", json_payload={"x": 2}, request_fn=legacy)
    assert resp.status_code == 204
    # single attempt because no TypeError thrown when timeout omitted in wrapper
    assert calls["attempts"] == 1


def test_resilient_get_normal():
    captured = {}

    def fake(url, params=None, headers=None, timeout=None, stream=None):
        captured["params"] = params
        r = MagicMock()
        r.status_code = 200
        r.text = "ok"
        return r

    resp = resilient_get("https://example.com", params={"q": "x"}, request_fn=fake)
    assert resp.status_code == 200
    assert captured["params"] == {"q": "x"}


def test_resilient_get_legacy_timeout_fallback():
    calls = {"attempts": 0}

    def legacy(url, params=None, headers=None, stream=None):  # no timeout
        calls["attempts"] += 1
        r = MagicMock()
        r.status_code = 200
        r.text = "ok"
        return r

    resp = resilient_get("https://example.com", params={"k": 1}, request_fn=legacy)
    assert resp.status_code == 200
    assert calls["attempts"] == 1
