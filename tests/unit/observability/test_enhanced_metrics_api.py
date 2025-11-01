from __future__ import annotations

import sys
import types
from datetime import datetime

import pytest


try:  # pragma: no cover - optional dependency for route tests
    from flask import Flask
except Exception:  # pragma: no cover - Flask not installed in some envs
    Flask = None  # type: ignore[misc,assignment]

from ultimate_discord_intelligence_bot.observability.enhanced_metrics_api import (
    EnhancedMetricsAPI,
)


class _FakeSample:
    def __init__(self, name: str, value: float, labels: dict[str, str] | None = None):
        self.name = name
        self.value = value
        self.labels = labels or {}


class _FakeFamily:
    def __init__(self, samples: list[_FakeSample]):
        self.samples = samples


class _FakeCounter:
    def __init__(self, metric_families: list[_FakeFamily], *, as_generator: bool = False):
        self._metric_families = metric_families
        self._as_generator = as_generator

    def collect(self):  # pragma: no cover - exercised via tests
        if self._as_generator:
            return (family for family in self._metric_families)
        return self._metric_families


@pytest.fixture
def enhanced_metrics_api() -> EnhancedMetricsAPI:
    # Bypass __init__ to avoid requiring Flask during tests.
    return object.__new__(EnhancedMetricsAPI)


def _install_fake_obs(monkeypatch: pytest.MonkeyPatch, counter: object) -> None:
    fake_obs_module = types.ModuleType("obs")
    fake_metrics_module = types.ModuleType("obs.metrics")
    fake_metrics_module.TRAJECTORY_EVALUATIONS = counter  # type: ignore[attr-defined]
    fake_obs_module.metrics = fake_metrics_module  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "obs", fake_obs_module)
    monkeypatch.setitem(sys.modules, "obs.metrics", fake_metrics_module)


def test_evaluation_metrics_aggregates_samples(
    monkeypatch: pytest.MonkeyPatch, enhanced_metrics_api: EnhancedMetricsAPI
) -> None:
    families = [
        _FakeFamily(
            [
                _FakeSample(
                    name="trajectory_evaluations_total",
                    value=3,
                    labels={"tenant": "tenant-a", "workspace": "ws-1", "success": "true"},
                ),
                _FakeSample(
                    name="trajectory_evaluations_total",
                    value=1,
                    labels={"tenant": "tenant-a", "workspace": "ws-1", "success": "false"},
                ),
                _FakeSample(
                    name="ignored_metric",
                    value=100,
                    labels={"tenant": "tenant-a", "workspace": "ws-1"},
                ),
            ]
        ),
        _FakeFamily(
            [
                _FakeSample(
                    name="trajectory_evaluations_total",
                    value=2,
                    labels={"tenant": "tenant-b", "workspace": "ws-2", "success": "1"},
                ),
            ]
        ),
    ]

    counter = _FakeCounter(families)
    _install_fake_obs(monkeypatch, counter)

    result = enhanced_metrics_api._get_trajectory_evaluation_metrics()

    assert result["enabled"] is True
    assert result["total"] == 6
    assert result["success_count"] == 5
    assert result["failure_count"] == 1
    assert pytest.approx(result["success_rate"], rel=1e-3) == pytest.approx(5 / 6, rel=1e-3)

    per_tenant = result["per_tenant"]
    assert len(per_tenant) == 2
    # Sorted by total descending
    assert per_tenant[0]["tenant"] == "tenant-a"
    assert per_tenant[0]["total"] == 4
    assert per_tenant[0]["success"] == 3
    assert per_tenant[0]["failure"] == 1
    assert pytest.approx(per_tenant[0]["success_rate"], rel=1e-3) == pytest.approx(3 / 4, rel=1e-3)

    assert per_tenant[1]["tenant"] == "tenant-b"
    assert per_tenant[1]["total"] == 2
    assert per_tenant[1]["success"] == 2
    assert per_tenant[1]["failure"] == 0

    # last_updated should be a valid ISO timestamp
    datetime.fromisoformat(result["last_updated"])


def test_evaluation_metrics_handles_generator_collect(
    monkeypatch: pytest.MonkeyPatch, enhanced_metrics_api: EnhancedMetricsAPI
) -> None:
    counter = _FakeCounter(
        [_FakeFamily([_FakeSample("trajectory_evaluations_total", 1, {"success": "yes"})])],
        as_generator=True,
    )
    _install_fake_obs(monkeypatch, counter)

    result = enhanced_metrics_api._get_trajectory_evaluation_metrics()

    assert result["enabled"] is True
    assert result["total"] == 1
    assert result["success_count"] == 1
    assert result["failure_count"] == 0


def test_evaluation_metrics_handles_missing_prometheus(
    monkeypatch: pytest.MonkeyPatch, enhanced_metrics_api: EnhancedMetricsAPI
) -> None:
    _install_fake_obs(monkeypatch, object())

    result = enhanced_metrics_api._get_trajectory_evaluation_metrics()

    assert result["enabled"] is False
    assert result["reason"] == "prometheus_unavailable"


def test_evaluation_metrics_handles_metrics_module_failure(
    monkeypatch: pytest.MonkeyPatch, enhanced_metrics_api: EnhancedMetricsAPI
) -> None:
    failing_obs_module = types.ModuleType("obs")

    def _raise_for_metrics(name: str) -> None:  # pragma: no cover - helper
        raise RuntimeError("metrics module missing")

    failing_obs_module.__getattr__ = _raise_for_metrics  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "obs", failing_obs_module)
    monkeypatch.delitem(sys.modules, "obs.metrics", raising=False)

    result = enhanced_metrics_api._get_trajectory_evaluation_metrics()

    assert result["enabled"] is False
    assert result["reason"] == "metrics_module_unavailable"


def test_evaluation_metrics_handles_missing_samples(
    monkeypatch: pytest.MonkeyPatch, enhanced_metrics_api: EnhancedMetricsAPI
) -> None:
    counter = _FakeCounter([_FakeFamily([_FakeSample("other_metric", 99)])])
    _install_fake_obs(monkeypatch, counter)

    result = enhanced_metrics_api._get_trajectory_evaluation_metrics()

    assert result["enabled"] is True
    assert result["total"] == 0
    assert result["success_count"] == 0
    assert result["failure_count"] == 0
    assert result["per_tenant"] == []


def test_evaluation_metrics_handles_none_collect_result(
    monkeypatch: pytest.MonkeyPatch, enhanced_metrics_api: EnhancedMetricsAPI
) -> None:
    class _NoneCounter:
        def collect(self):  # pragma: no cover - simple stub
            return None

    _install_fake_obs(monkeypatch, _NoneCounter())

    result = enhanced_metrics_api._get_trajectory_evaluation_metrics()

    assert result["enabled"] is True
    assert result["total"] == 0
    assert result["success_count"] == 0
    assert result["failure_count"] == 0
    assert result["per_tenant"] == []


@pytest.mark.skipif(Flask is None, reason="Flask is required for route tests")
def test_get_evaluation_metrics_route_returns_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_payload = {
        "enabled": True,
        "total": 42,
        "success_count": 40,
        "failure_count": 2,
        "success_rate": 40 / 42,
        "per_tenant": [
            {
                "tenant": "tenant-x",
                "workspace": "ws-main",
                "total": 42,
                "success": 40,
                "failure": 2,
                "success_rate": 40 / 42,
            }
        ],
        "last_updated": datetime.now().isoformat(),
    }

    assert Flask is not None  # for mypy / type checkers
    app = Flask(__name__)
    api = EnhancedMetricsAPI(app)

    monkeypatch.setattr(
        api,
        "_get_trajectory_evaluation_metrics",
        lambda: expected_payload,
        raising=False,
    )

    client = api.app.test_client()
    response = client.get("/api/metrics/evaluations")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {"status": "success", "data": expected_payload}


@pytest.mark.skipif(Flask is None, reason="Flask is required for route tests")
def test_get_evaluation_metrics_route_handles_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    assert Flask is not None
    app = Flask(__name__)
    api = EnhancedMetricsAPI(app)

    def _boom() -> dict[str, object]:  # pragma: no cover - helper
        raise RuntimeError("boom")

    monkeypatch.setattr(api, "_get_trajectory_evaluation_metrics", _boom, raising=False)

    client = api.app.test_client()
    response = client.get("/api/metrics/evaluations")

    assert response.status_code == 500
    payload = response.get_json()
    assert payload["status"] == "error"
    assert "boom" in payload["error"]
