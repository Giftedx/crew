import numpy as np
import pytest

from ultimate_discord_intelligence_bot.obs import metrics
from ultimate_discord_intelligence_bot.services.rl_model_router import (
    RLModelRouter,
    RoutingReward,
    TaskComplexity,
    TrajectoryFeedback,
)


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


@pytest.fixture
def router_metric_stubs(monkeypatch):
    queue_depth = _GaugeStub()
    processed = _CounterStub()
    failed = _CounterStub()
    trajectory_processed = _CounterStub()
    base_labels = {"tenant": "test-tenant", "workspace": "test-workspace"}
    monkeypatch.setattr(metrics, "RL_FEEDBACK_QUEUE_DEPTH", queue_depth)
    monkeypatch.setattr(metrics, "RL_FEEDBACK_PROCESSED", processed)
    monkeypatch.setattr(metrics, "RL_FEEDBACK_FAILED", failed)
    monkeypatch.setattr(metrics, "TRAJECTORY_FEEDBACK_PROCESSED", trajectory_processed)

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
        "trajectory_processed": trajectory_processed,
        "labels": base_labels,
    }


class _BanditStub:
    def __init__(self):
        self.calls: list[tuple[str, np.ndarray, float, TrajectoryFeedback]] = []

    def update(
        self, model_id: str, context: np.ndarray, reward: float, trajectory_feedback: TrajectoryFeedback | None = None
    ) -> None:
        self.calls.append((model_id, context, reward, trajectory_feedback))


class _BanditExceptionStub(_BanditStub):
    def update(
        self, model_id: str, context: np.ndarray, reward: float, trajectory_feedback: TrajectoryFeedback | None = None
    ) -> None:
        super().update(model_id, context, reward, trajectory_feedback)
        raise RuntimeError("update failed")


def _make_reward(task_id: str, model_id: str) -> RoutingReward:
    return RoutingReward(
        model_id=model_id,
        task_id=task_id,
        reward=0.8,
        latency_ms=120.0,
        cost_usd=0.02,
        quality_score=0.9,
        success=True,
        context={"complexity": TaskComplexity.MODERATE.value, "token_estimate": 800},
    )


def _make_feedback(task_id: str, model_id: str, success: bool = True) -> TrajectoryFeedback:
    return TrajectoryFeedback(
        trajectory_id=task_id,
        model_id=model_id,
        accuracy_score=0.85 if success else 0.45,
        efficiency_score=0.8 if success else 0.4,
        error_handling_score=0.82 if success else 0.5,
        overall_score=0.83 if success else 0.45,
        trajectory_length=12,
        success=success,
        reasoning="ok" if success else "missing context",
    )


def test_process_trajectory_feedback_success_and_missing_history(router_metric_stubs):
    router = RLModelRouter()
    bandit = _BanditStub()
    router.bandit = bandit
    router.routing_history = [_make_reward(task_id="task-1", model_id="gpt-4")]
    success_feedback = _make_feedback(task_id="task-1", model_id="gpt-4", success=True)
    missing_feedback = _make_feedback(task_id="task-2", model_id="gpt-4", success=False)
    router.trajectory_feedback_queue.extend([success_feedback, missing_feedback])
    result = router.process_trajectory_feedback(batch_size=2)
    assert result.success
    assert result.data["processed"] == 1
    assert result.data["failed"] == 1
    assert result.data["remaining_queue_size"] == 0
    labels = router_metric_stubs["labels"]
    assert router_metric_stubs["queue_depth"].get(**labels) == 0
    assert router_metric_stubs["processed"].get(**labels, result="success") == 1
    assert router_metric_stubs["processed"].get(**labels, result="missing_history") == 1
    assert router_metric_stubs["failed"].get(**labels, reason="missing_history") == 1
    assert router_metric_stubs["trajectory_processed"].get(**labels, model_id="gpt-4", result="success") == 1
    assert router_metric_stubs["trajectory_processed"].get(**labels, model_id="gpt-4", result="missing_history") == 1
    assert len(router.trajectory_feedback_queue) == 0
    assert len(bandit.calls) == 1
    model_id, context_vector, reward_value, feedback = bandit.calls[0]
    assert model_id == "gpt-4"
    assert isinstance(context_vector, np.ndarray)
    assert pytest.approx(reward_value) == 0.8
    assert feedback is success_feedback


def test_process_trajectory_feedback_bandit_not_initialized(router_metric_stubs):
    router = RLModelRouter()
    router.bandit = None
    router.trajectory_feedback_queue.append(_make_feedback("task-1", "gpt-4"))
    result = router.process_trajectory_feedback()
    labels = router_metric_stubs["labels"]
    assert not result.success
    assert result.error == "Bandit not initialized"
    assert router_metric_stubs["queue_depth"].get(**labels) == 1
    assert router_metric_stubs["failed"].get(**labels, reason="bandit_not_initialized") == 1
    assert router_metric_stubs["processed"].children == {}
    assert router_metric_stubs["trajectory_processed"].children == {}
    assert len(router.trajectory_feedback_queue) == 1


def test_process_trajectory_feedback_empty_queue(router_metric_stubs):
    router = RLModelRouter()
    result = router.process_trajectory_feedback()
    labels = router_metric_stubs["labels"]
    assert result.skipped
    assert result.data["reason"] == "No trajectory feedback available"
    assert router_metric_stubs["queue_depth"].get(**labels) == 0
    assert router_metric_stubs["processed"].children == {}
    assert router_metric_stubs["failed"].children == {}
    assert router_metric_stubs["trajectory_processed"].children == {}


def test_process_trajectory_feedback_update_exception(router_metric_stubs):
    router = RLModelRouter()
    router.bandit = _BanditExceptionStub()
    router.routing_history = [_make_reward(task_id="task-1", model_id="gpt-4")]
    router.trajectory_feedback_queue.append(_make_feedback("task-1", "gpt-4"))
    result = router.process_trajectory_feedback(batch_size=1)
    labels = router_metric_stubs["labels"]
    assert result.success
    assert result.data["processed"] == 0
    assert result.data["failed"] == 1
    assert result.data["remaining_queue_size"] == 0
    assert router_metric_stubs["queue_depth"].get(**labels) == 0
    assert router_metric_stubs["processed"].get(**labels, result="failure") == 1
    assert router_metric_stubs["failed"].get(**labels, reason="exception") == 1
    assert router_metric_stubs["trajectory_processed"].get(**labels, model_id="gpt-4", result="failure") == 1
    assert len(router.trajectory_feedback_queue) == 0
