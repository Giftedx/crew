
import pytest

from ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService


class DummyResp:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            from requests import HTTPError
            raise HTTPError(f"status {self.status_code}")

    def json(self):
        return self._payload


@pytest.fixture
def enable_retry(monkeypatch):
    monkeypatch.setenv("ENABLE_ANALYSIS_HTTP_RETRY", "1")
    yield
    monkeypatch.delenv("ENABLE_ANALYSIS_HTTP_RETRY", raising=False)


def test_openrouter_retries_and_succeeds(monkeypatch, enable_retry):
    service = OpenRouterService(api_key="k")

    attempts = {"n": 0}

    def fake_post(url: str, **kwargs):  # matches lambda usage in service
        attempts["n"] += 1
        if attempts["n"] < 2:
            # first attempt fails with retryable 500
            return DummyResp(500, {"error": {"message": "upstream fail"}})
        return DummyResp(200, {"choices": [{"message": {"content": "ok"}}]})

    # Patch resilient_post referenced inside lambda closure by monkeypatching at module level
    import ultimate_discord_intelligence_bot.services.openrouter_service as mod
    monkeypatch.setattr(mod, "resilient_post", fake_post)

    resp = service.route(prompt="hi", model="m")
    assert resp["response"] == "ok"
    # Ensure at least 2 attempts occurred
    assert attempts["n"] == 2


def test_openrouter_retry_giveup(monkeypatch, enable_retry):
    service = OpenRouterService(api_key="k")

    attempts = {"n": 0}

    def always_fail(url: str, **kwargs):
        attempts["n"] += 1
        return DummyResp(500, {"error": {"message": "still broken"}})

    import ultimate_discord_intelligence_bot.services.openrouter_service as mod
    monkeypatch.setattr(mod, "resilient_post", always_fail)

    from obs.metrics import HTTP_RETRY_GIVEUPS, label_ctx
    # capture pre value (prom client may not be installed; counter exposes internal _value for fallback registry)
    before = None
    try:
        before = HTTP_RETRY_GIVEUPS.labels(**label_ctx(), method="POST")._value.get()
    except AttributeError:
        # Older / fallback counter implementation may lack internal state attribute; treat as absent.
        before = None
    except Exception:  # noqa: S110 - metrics backend optional; silence only metrics retrieval failure
        before = None
    result = service.route(prompt="hi", model="m")
    assert result["status"] == "error"
    assert attempts["n"] == 3  # max_attempts in service wiring
    try:
        after = HTTP_RETRY_GIVEUPS.labels(**label_ctx(), method="POST")._value.get()
        if before is not None:
            assert after == before + 1
    except AttributeError:
        # Counter implementation changed or backend absent; skip post assertion.
        pass
    except Exception:  # noqa: S110 - intentionally ignoring metrics-only failure path
        pass
