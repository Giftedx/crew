from __future__ import annotations

import logging
import re

import pytest

from obs import metrics as metrics_mod
from ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService


def _reset_metrics():
    try:
        metrics_mod.reset()
    except Exception as exc:  # pragma: no cover - metrics backend optional
        logging.debug("metrics.reset() unavailable: %s", exc)


def test_openrouter_non_strict_fallback_increments_metric(monkeypatch):
    # Ensure non-strict mode
    monkeypatch.delenv("ENABLE_TENANCY_STRICT", raising=False)
    monkeypatch.setenv("ENABLE_INGEST_STRICT", "0")

    _reset_metrics()

    # Force offline mode to avoid network
    svc = OpenRouterService(api_key="")
    # No tenant context set -> should fallback and increment metric
    res = svc.route("ping")
    assert res["status"] == "success"

    data = metrics_mod.render().decode("utf-8")
    if data:
        assert "tenancy_fallback_total" in data
        # Component label should be openrouter_service
        assert re.search(r"component=\"openrouter_service\"", data) is not None


def test_openrouter_strict_mode_requires_tenant(monkeypatch):
    # Enable strict tenancy
    monkeypatch.setenv("ENABLE_TENANCY_STRICT", "1")
    monkeypatch.setenv("ENABLE_INGEST_STRICT", "1")

    _reset_metrics()

    svc = OpenRouterService(api_key="")
    with pytest.raises(RuntimeError):
        svc.route("ping")
