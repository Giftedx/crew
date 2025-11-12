from __future__ import annotations

import importlib
from typing import Any

import pytest

from platform.cache import tool_cache_decorator


class _FakeCounter:
    def __init__(self) -> None:
        self.value = 0.0

    def inc(self, amount: float = 1.0) -> None:
        self.value += amount


class _FakeMetrics:
    def __init__(self) -> None:
        self.counters: dict[tuple[str, tuple[tuple[str, str], ...]], _FakeCounter] = {}

    def counter(self, name: str, *_args: Any, labels: dict[str, str] | None = None, **_kwargs: Any) -> _FakeCounter:
        key = (name, tuple(sorted((labels or {}).items())))
        if key not in self.counters:
            self.counters[key] = _FakeCounter()
        return self.counters[key]


class _FakeCache:
    def __init__(self) -> None:
        self.store: dict[tuple[str, tuple[tuple[str, str], ...], str, str], Any] = {}
        self.get_calls: list[dict[str, Any]] = []
        self.set_calls: list[dict[str, Any]] = []

    def _key(self, operation: str, inputs: dict[str, str], tenant: str, workspace: str) -> tuple[str, tuple[tuple[str, str], ...], str, str]:
        return (operation, tuple(sorted(inputs.items())), tenant, workspace)

    def get(self, operation: str, inputs: dict[str, str], tenant: str = "", workspace: str = "") -> Any | None:
        self.get_calls.append({"operation": operation, "inputs": dict(inputs), "tenant": tenant, "workspace": workspace})
        key = self._key(operation, inputs, tenant, workspace)
        return self.store.get(key)

    def set(
        self,
        operation: str,
        inputs: dict[str, str],
        value: Any,
        ttl: int | None = None,
        tenant: str = "",
        workspace: str = "",
    ) -> bool:
        self.set_calls.append(
            {
                "operation": operation,
                "inputs": dict(inputs),
                "ttl": ttl,
                "tenant": tenant,
                "workspace": workspace,
            }
        )
        key = self._key(operation, inputs, tenant, workspace)
        self.store[key] = value
        return True


class _FakeCacheFactory:
    def __init__(self) -> None:
        self.instance = _FakeCache()

    def __call__(self, *_args: Any, **_kwargs: Any) -> _FakeCache:
        return self.instance


def _counter_total(metrics: _FakeMetrics, name: str, namespace: str) -> float:
    key = (name, tuple(sorted({"namespace": namespace}.items())))
    counter = metrics.counters.get(key)
    return counter.value if counter else 0.0


def _reload_with_fake_cache(
    module_name: str,
    *,
    monkeypatch: pytest.MonkeyPatch,
    cache_factory: _FakeCacheFactory,
    metrics: _FakeMetrics,
) -> Any:
    module = importlib.import_module(module_name)
    monkeypatch.setattr(tool_cache_decorator, "MultiLevelCache", cache_factory)
    monkeypatch.setattr(tool_cache_decorator, "get_metrics", lambda: metrics)
    return importlib.reload(module)


def _restore_module(module_name: str) -> None:
    module = importlib.import_module(module_name)
    importlib.reload(module)


def test_enhanced_analysis_tool_uses_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    cache_factory = _FakeCacheFactory()
    metrics = _FakeMetrics()
    module_name = "domains.intelligence.analysis.enhanced_analysis_tool"

    module = _reload_with_fake_cache(
        module_name,
        monkeypatch=monkeypatch,
        cache_factory=cache_factory,
        metrics=metrics,
    )

    tool = module.EnhancedAnalysisTool()

    first = tool._run("Policy changes improve healthcare", tenant="tenant-a", workspace="workspace-a")
    second = tool._run("Policy changes improve healthcare", tenant="tenant-a", workspace="workspace-a")

    assert first.success is True
    assert first.metadata["cache_hit"] is False
    assert second.metadata["cache_hit"] is True
    assert first.metadata["cache_key"] == second.metadata["cache_key"]

    assert cache_factory.instance.set_calls
    assert cache_factory.instance.get_calls[-1]["inputs"]["cache_key"] == first.metadata["cache_key"]

    namespace = "tool:enhanced_analysis"
    assert _counter_total(metrics, "tool_cache_misses_total", namespace) == 1.0
    assert _counter_total(metrics, "tool_cache_hits_total", namespace) == 1.0

    monkeypatch.undo()
    _restore_module(module_name)


def test_text_analysis_tool_uses_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    cache_factory = _FakeCacheFactory()
    metrics = _FakeMetrics()
    module_name = "domains.intelligence.analysis.text_analysis_tool"

    monkeypatch.setenv("ALLOW_NLTK_DEGRADED_MODE", "1")
    module = _reload_with_fake_cache(
        module_name,
        monkeypatch=monkeypatch,
        cache_factory=cache_factory,
        metrics=metrics,
    )

    tool = module.TextAnalysisTool()

    sample_text = "This project is fantastic and shows excellent progress"
    first = tool._run(sample_text)
    second = tool._run(sample_text)

    assert first.success is True
    assert first.metadata["cache_hit"] is False
    assert second.metadata["cache_hit"] is True
    assert first.metadata["cache_key"] == second.metadata["cache_key"]

    namespace = "tool:text_analysis"
    assert _counter_total(metrics, "tool_cache_misses_total", namespace) == 1.0
    assert _counter_total(metrics, "tool_cache_hits_total", namespace) == 1.0

    monkeypatch.undo()
    _restore_module(module_name)


def test_sentiment_tool_uses_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    cache_factory = _FakeCacheFactory()
    metrics = _FakeMetrics()
    module_name = "domains.intelligence.analysis.sentiment_tool"

    module = _reload_with_fake_cache(
        module_name,
        monkeypatch=monkeypatch,
        cache_factory=cache_factory,
        metrics=metrics,
    )

    tool = module.SentimentTool()

    first = tool._run("I love the direction of this project")
    second = tool._run("I love the direction of this project")

    assert first.success is True
    assert first.metadata["cache_hit"] is False
    assert second.metadata["cache_hit"] is True
    assert first.metadata["cache_key"] == second.metadata["cache_key"]

    namespace = "tool:sentiment"
    assert _counter_total(metrics, "tool_cache_misses_total", namespace) == 1.0
    assert _counter_total(metrics, "tool_cache_hits_total", namespace) == 1.0

    monkeypatch.undo()
    _restore_module(module_name)