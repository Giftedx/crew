import asyncio
from types import SimpleNamespace

from ultimate_discord_intelligence_bot.pipeline import ContentPipeline


def _run(coro):
    return asyncio.run(coro)


def test_run_with_retries_rate_limit_then_success(monkeypatch):
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] == 1:
            return {"status": "error", "status_code": 429, "error": "rate limited"}
        return {"status": "success", "ok": True}

    # speed up sleep
    async def _noop_sleep(_s, *a, **k):
        return None

    monkeypatch.setattr(asyncio, "sleep", _noop_sleep)

    pipe = ContentPipeline(
        downloader=SimpleNamespace(),
        transcriber=SimpleNamespace(),
        analyzer=SimpleNamespace(),
        drive=None,
        discord=None,
        fallacy_detector=None,
        perspective=None,
        memory=None,
    )
    res = _run(pipe._run_with_retries(fn, step="test", attempts=2, delay=0.01))
    assert res.success is True
    assert calls["n"] == 2


def test_run_with_retries_permanent_no_retry(monkeypatch):
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        return {"status": "error", "status_code": 400, "error": "bad request"}

    async def _noop_sleep(_s, *a, **k):
        return None

    monkeypatch.setattr(asyncio, "sleep", _noop_sleep)

    pipe = ContentPipeline(downloader=SimpleNamespace())
    res = _run(pipe._run_with_retries(fn, step="test", attempts=3, delay=0.01))
    assert res.success is False
    assert calls["n"] == 1


def test_run_with_retries_transient_retries(monkeypatch):
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] < 3:
            return {"status": "error", "error": "timeout"}
        return {"status": "success", "ok": True}

    async def _fast_sleep(_s):
        return None

    monkeypatch.setattr(asyncio, "sleep", _fast_sleep)

    pipe = ContentPipeline(downloader=SimpleNamespace())
    res = _run(pipe._run_with_retries(fn, step="test", attempts=3, delay=0.01))
    assert res.success is True
    assert calls["n"] == 3
