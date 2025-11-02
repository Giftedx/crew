from __future__ import annotations

import contextlib
import re

from obs import metrics as metrics_mod
from ultimate_discord_intelligence_bot.services.openrouter_service import (
    OpenRouterService,
)


def test_openrouter_metrics_use_effective_labels_non_strict(monkeypatch):
    # Ensure non-strict tenancy so service will fallback to default:main without raising
    monkeypatch.delenv("ENABLE_TENANCY_STRICT", raising=False)
    monkeypatch.setenv("ENABLE_INGEST_STRICT", "0")

    # Reset metrics to a clean state
    with contextlib.suppress(Exception):
        metrics_mod.reset()

    # Force offline mode to avoid network and make behavior deterministic
    svc = OpenRouterService(api_key="")
    res = svc.route("hello world")
    assert res["status"] == "success"

    # Render metrics and ensure LLM metrics are labeled with effective tenant/workspace (default:main)
    data = metrics_mod.render().decode("utf-8") if hasattr(metrics_mod, "render") else ""

    if not data:
        # If prometheus backend is not available, we can't assert on exposition text; skip assertions
        return

    # llm_model_selected_total should include tenant/workspace labels from effective context, not unknown
    assert re.search(r'llm_model_selected_total\{[^}]*tenant="default"[^}]*workspace="main"', data), data

    # llm_estimated_cost_usd is a histogram; check any of its series include correct labels
    assert re.search(
        r'llm_estimated_cost_usd(_bucket|_sum|_count)?\{[^}]*tenant="default"[^}]*workspace="main"',
        data,
    ), data

    # llm_latency_ms histogram labels should also carry effective tenant/workspace
    assert re.search(
        r'llm_latency_ms(_bucket|_sum|_count)?\{[^}]*tenant="default"[^}]*workspace="main"',
        data,
    ), data
