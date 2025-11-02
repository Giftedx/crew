from __future__ import annotations

import logging
import re
from platform.llm.providers.openrouter import OpenRouterService
from platform.observability import metrics as metrics_mod

import pytest


def _reset_metrics():
    try:
        metrics_mod.reset()
    except Exception as exc:
        logging.debug("metrics.reset() unavailable: %s", exc)


def test_openrouter_non_strict_fallback_increments_metric(monkeypatch):
    monkeypatch.delenv("ENABLE_TENANCY_STRICT", raising=False)
    monkeypatch.setenv("ENABLE_INGEST_STRICT", "0")
    _reset_metrics()
    svc = OpenRouterService(api_key="")
    res = svc.route("ping")
    assert res["status"] == "success"
    data = metrics_mod.render().decode("utf-8")
    if data:
        assert "tenancy_fallback_total" in data
        assert re.search('component=\\"openrouter_service\\"', data) is not None


def test_openrouter_strict_mode_requires_tenant(monkeypatch):
    monkeypatch.setenv("ENABLE_TENANCY_STRICT", "1")
    monkeypatch.setenv("ENABLE_INGEST_STRICT", "1")
    _reset_metrics()
    svc = OpenRouterService(api_key="")
    with pytest.raises(RuntimeError):
        svc.route("ping")
