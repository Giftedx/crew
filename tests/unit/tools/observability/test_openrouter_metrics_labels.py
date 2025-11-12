from __future__ import annotations

import contextlib
import re
from platform.llm.providers.openrouter import OpenRouterService

from ultimate_discord_intelligence_bot.obs import metrics as metrics_mod


def test_openrouter_metrics_use_effective_labels_non_strict(monkeypatch):
    monkeypatch.delenv("ENABLE_TENANCY_STRICT", raising=False)
    monkeypatch.setenv("ENABLE_INGEST_STRICT", "0")
    with contextlib.suppress(Exception):
        metrics_mod.reset()
    svc = OpenRouterService(api_key="")
    res = svc.route("hello world")
    assert res["status"] == "success"
    data = metrics_mod.render().decode("utf-8") if hasattr(metrics_mod, "render") else ""
    if not data:
        return
    assert re.search('llm_model_selected_total\\{[^}]*tenant="default"[^}]*workspace="main"', data), data
    assert re.search(
        'llm_estimated_cost_usd(_bucket|_sum|_count)?\\{[^}]*tenant="default"[^}]*workspace="main"', data
    ), data
    assert re.search('llm_latency_ms(_bucket|_sum|_count)?\\{[^}]*tenant="default"[^}]*workspace="main"', data), data
