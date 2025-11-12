import sys
import types
from collections.abc import Callable

import pytest

from ultimate_discord_intelligence_bot.obs import metrics
from ultimate_discord_intelligence_bot.obs.enhanced_monitoring import EnhancedMonitoringSystem
from ultimate_discord_intelligence_bot.step_result import StepResult


class _CounterChild:
    def __init__(self, labels: dict[str, str]):
        self.labels = labels
        self.value = 0

    def inc(self, amount: int = 1) -> None:
        self.value += amount


class _CounterStub:
    def __init__(self):
        self.children: dict[tuple[tuple[str, str], ...], _CounterChild] = {}

    def labels(self, **labels: str) -> _CounterChild:
        key = tuple(sorted(labels.items()))
        child = self.children.get(key)
        if child is None:
            child = _CounterChild(labels)
            self.children[key] = child
        return child

    def get(self, **labels: str) -> int:
        key = tuple(sorted(labels.items()))
        child = self.children.get(key)
        return child.value if child else 0


class _GaugeChild:
    def __init__(self, labels: dict[str, str]):
        self.labels = labels
        self.value: float = 0.0

    def set(self, value: float) -> None:
        self.value = value


class _GaugeStub:
    def __init__(self):
        self.children: dict[tuple[tuple[str, str], ...], _GaugeChild] = {}

    def labels(self, **labels: str) -> _GaugeChild:
        key = tuple(sorted(labels.items()))
        child = self.children.get(key)
        if child is None:
            child = _GaugeChild(labels)
            self.children[key] = child
        return child

    def get(self, **labels: str) -> float:
        key = tuple(sorted(labels.items()))
        child = self.children.get(key)
        return child.value if child else 0.0


class _HistogramChild:
    def __init__(self, labels: dict[str, str]):
        self.labels = labels
        self.values: list[float] = []

    def observe(self, value: float) -> None:
        self.values.append(value)


class _HistogramStub:
    def __init__(self):
        self.children: dict[tuple[tuple[str, str], ...], _HistogramChild] = {}

    def labels(self, **labels: str) -> _HistogramChild:
        key = tuple(sorted(labels.items()))
        child = self.children.get(key)
        if child is None:
            child = _HistogramChild(labels)
            self.children[key] = child
        return child

    def get_values(self, **labels: str) -> list[float]:
        key = tuple(sorted(labels.items()))
        child = self.children.get(key)
        return list(child.values) if child else []


@pytest.fixture
def rl_metric_stubs(monkeypatch):
    queue_depth = _GaugeStub()
    processed = _CounterStub()
    failed = _CounterStub()
    latency = _HistogramStub()
    base_labels = {"tenant": "test-tenant", "workspace": "test-workspace"}
    monkeypatch.setattr(metrics, "RL_FEEDBACK_QUEUE_DEPTH", queue_depth)
    monkeypatch.setattr(metrics, "RL_FEEDBACK_PROCESSED", processed)
    monkeypatch.setattr(metrics, "RL_FEEDBACK_FAILED", failed)
    monkeypatch.setattr(metrics, "RL_FEEDBACK_PROCESSING_LATENCY", latency)

    def _label_ctx(extra_labels: dict[str, str] | None = None) -> dict[str, str]:
        merged = dict(base_labels)
        if extra_labels:
            merged.update(extra_labels)
        return merged

    monkeypatch.setattr(metrics, "label_ctx", _label_ctx)
    return {
        "queue_depth": queue_depth,
        "processed": processed,
        "failed": failed,
        "latency": latency,
        "labels": base_labels,
    }


class _FakeRouter:
    def __init__(
        self,
        initial_items: int = 0,
        result_factory: Callable[[int, int, int], StepResult] | None = None,
        raise_exc: Exception | None = None,
    ):
        self.trajectory_feedback_queue = [object()] * int(initial_items)
        self._result_factory = result_factory
        self._raise_exc = raise_exc
        self.last_batch_size: int | None = None

    def process_trajectory_feedback(self, batch_size: int = 10):
        self.last_batch_size = batch_size
        if self._raise_exc is not None:
            raise self._raise_exc
        take = min(batch_size, len(self.trajectory_feedback_queue))
        self.trajectory_feedback_queue = self.trajectory_feedback_queue[take:]
        if self._result_factory is not None:
            return self._result_factory(batch_size, take, len(self.trajectory_feedback_queue))
        return StepResult.ok(processed=take, failed=0, remaining_queue_size=len(self.trajectory_feedback_queue))


def _install_registry_stub(router: _FakeRouter | None) -> None:
    """Install a stubbed rl_router_registry module to avoid importing heavy deps."""
    pkg_name = "ultimate_discord_intelligence_bot.services"
    mod_name = pkg_name + ".rl_router_registry"
    if pkg_name not in sys.modules:
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = []
        sys.modules[pkg_name] = pkg
    stub = types.ModuleType(mod_name)
    stub._router = router

    def get_rl_model_router(create_if_missing: bool = False):
        return getattr(stub, "_router", None)

    def set_rl_model_router(new_router):
        stub._router = new_router

    stub.get_rl_model_router = get_rl_model_router
    stub.set_rl_model_router = set_rl_model_router
    sys.modules[mod_name] = stub


@pytest.fixture(autouse=True)
def _cleanup_registry_modules():
    yield
    for name in list(sys.modules.keys()):
        if name.startswith("ultimate_discord_intelligence_bot.services.rl_router_registry"):
            sys.modules.pop(name, None)


def test_process_once_flag_disabled(monkeypatch, rl_metric_stubs):
    monkeypatch.setenv("ENABLE_TRAJECTORY_FEEDBACK_LOOP", "0")
    router = _FakeRouter(initial_items=3)
    _install_registry_stub(router)
    ems = EnhancedMonitoringSystem()
    summary = ems.process_rl_feedback_once()
    assert summary["status"] == "disabled"
    assert summary["processed"] == 0
    assert summary["failed"] == 0
    assert summary["queue_depth"] == 3
    assert len(router.trajectory_feedback_queue) == 3
    base_labels = rl_metric_stubs["labels"]
    assert rl_metric_stubs["queue_depth"].get(**base_labels) == 3
    assert rl_metric_stubs["processed"].children == {}
    assert rl_metric_stubs["failed"].children == {}
    assert rl_metric_stubs["latency"].get_values(**base_labels) == []


def test_process_once_no_router_records_failure(monkeypatch, rl_metric_stubs):
    monkeypatch.setenv("ENABLE_TRAJECTORY_FEEDBACK_LOOP", "1")
    _install_registry_stub(None)
    ems = EnhancedMonitoringSystem()
    summary = ems.process_rl_feedback_once()
    assert summary["status"] == "no_router"
    assert summary["processed"] == 0
    assert summary["failed"] == 0
    assert summary["queue_depth"] == 0
    base_labels = rl_metric_stubs["labels"]
    assert rl_metric_stubs["queue_depth"].get(**base_labels) == 0
    assert rl_metric_stubs["failed"].get(**base_labels, reason="no_router") == 1


def test_process_once_exception_records_failure(monkeypatch, rl_metric_stubs):
    monkeypatch.setenv("ENABLE_TRAJECTORY_FEEDBACK_LOOP", "1")
    router = _FakeRouter(initial_items=4, raise_exc=RuntimeError("boom"))
    _install_registry_stub(router)
    ems = EnhancedMonitoringSystem()
    summary = ems.process_rl_feedback_once()
    assert summary["status"] == "error"
    assert summary["error"] == "boom"
    assert summary["processed"] == 0
    assert summary["failed"] == 0
    assert summary["queue_depth"] == 4
    assert len(router.trajectory_feedback_queue) == 4
    assert router.last_batch_size == 25
    base_labels = rl_metric_stubs["labels"]
    assert rl_metric_stubs["queue_depth"].get(**base_labels) == 4
    assert rl_metric_stubs["failed"].get(**base_labels, reason="exception") == 1
    assert rl_metric_stubs["processed"].children == {}
    assert rl_metric_stubs["latency"].get_values(**base_labels) == []


def test_process_once_success_records_metrics(monkeypatch, rl_metric_stubs):
    monkeypatch.setenv("ENABLE_TRAJECTORY_FEEDBACK_LOOP", "1")
    monkeypatch.setenv("RL_FEEDBACK_BATCH_SIZE", "2")
    metadata = {"batch_id": "batch-test"}

    def _result_factory(batch_size: int, processed: int, remaining: int) -> StepResult:
        result = StepResult.ok(processed=processed, failed=1, remaining_queue_size=remaining)
        result.metadata.update(metadata)
        return result

    router = _FakeRouter(initial_items=5, result_factory=_result_factory)
    _install_registry_stub(router)
    perf_values = iter([10.0, 10.123])
    monkeypatch.setattr("obs.enhanced_monitoring.time.perf_counter", lambda: next(perf_values))
    ems = EnhancedMonitoringSystem()
    summary = ems.process_rl_feedback_once(labels={"unit": "test"})
    merged_labels = {**rl_metric_stubs["labels"], "unit": "test"}
    assert summary["status"] == "success"
    assert summary["batch_size"] == 2
    assert summary["processed"] == 2
    assert summary["failed"] == 1
    assert summary["queue_depth"] == 3
    assert summary["metadata"] == metadata
    assert summary["latency_ms"] == pytest.approx(123.0, rel=0.001)
    assert router.last_batch_size == 2
    assert len(router.trajectory_feedback_queue) == 3
    assert rl_metric_stubs["queue_depth"].get(**merged_labels) == 3
    assert rl_metric_stubs["failed"].children == {}
    latency_samples = rl_metric_stubs["latency"].get_values(**merged_labels)
    assert len(latency_samples) == 1
    assert latency_samples[0] == pytest.approx(123.0, rel=1e-05)


def test_process_once_step_failure_records_metrics(monkeypatch, rl_metric_stubs):
    monkeypatch.setenv("ENABLE_TRAJECTORY_FEEDBACK_LOOP", "1")

    def _result_factory(batch_size: int, processed: int, remaining: int) -> StepResult:
        return StepResult.fail("router failure")

    router = _FakeRouter(initial_items=1, result_factory=_result_factory)
    _install_registry_stub(router)
    ems = EnhancedMonitoringSystem()
    summary = ems.process_rl_feedback_once()
    base_labels = rl_metric_stubs["labels"]
    assert summary["status"] == "error"
    assert summary["error"] == "router failure"
    assert summary["queue_depth"] == 1
    assert rl_metric_stubs["queue_depth"].get(**base_labels) == 1
    assert rl_metric_stubs["failed"].get(**base_labels, reason="step_failure") == 1
    assert rl_metric_stubs["processed"].children == {}
    assert len(router.trajectory_feedback_queue) == 0
