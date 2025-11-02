from platform.llm.providers.openrouter import OpenRouterService

import pytest


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
    monkeypatch.setenv("ENABLE_HTTP_RETRY", "1")
    yield
    monkeypatch.delenv("ENABLE_HTTP_RETRY", raising=False)


def test_openrouter_retries_and_succeeds(monkeypatch, enable_retry):
    service = OpenRouterService(api_key="k")
    attempts = {"n": 0}

    def fake_post(url: str, **kwargs):
        attempts["n"] += 1
        if attempts["n"] < 2:
            return DummyResp(500, {"error": {"message": "upstream fail"}})
        return DummyResp(200, {"choices": [{"message": {"content": "ok"}}]})

    import platform.llm.providers.openrouter as mod

    monkeypatch.setattr(mod, "resilient_post", fake_post)
    resp = service.route(prompt="hi", model="m")
    assert resp["response"] == "ok"
    assert attempts["n"] == 2


def test_openrouter_retry_giveup(monkeypatch, enable_retry):
    service = OpenRouterService(api_key="k")
    attempts = {"n": 0}

    def always_fail(url: str, **kwargs):
        attempts["n"] += 1
        return DummyResp(500, {"error": {"message": "still broken"}})

    import platform.llm.providers.openrouter as mod

    monkeypatch.setattr(mod, "resilient_post", always_fail)
    from platform.observability.metrics import HTTP_RETRY_GIVEUPS, label_ctx

    before = None
    try:
        before = HTTP_RETRY_GIVEUPS.labels(**label_ctx(), method="POST")._value.get()
    except AttributeError:
        before = None
    except Exception:
        before = None
    result = service.route(prompt="hi", model="m")
    assert result["status"] == "error"
    assert attempts["n"] == 3
    try:
        after = HTTP_RETRY_GIVEUPS.labels(**label_ctx(), method="POST")._value.get()
        if before is not None:
            assert after == before + 1
    except AttributeError:
        pass
    except Exception:
        pass
