from __future__ import annotations

"""RL-driven helper for selecting and executing tool plans.

The function :func:`execute_plan` accepts a mapping of plan labels to a
sequence of tool callables. Each tool callable must return a tuple of
``(outcome, signals)`` where ``outcome`` contains cost and latency metrics
and ``signals`` holds quality indicators. The helper delegates the choice of
plan to the reinforcement learning core via :func:`core.learn.learn` under
 the ``tool_planning`` domain.

Example
-------
>>> def tool() -> tuple[dict, dict]:
...     return {"cost_usd": 0.1, "latency_ms": 10}, {"success": 1.0}
>>> execute_plan({"demo": [tool]}, {"strategy": "demo"})

"""

from typing import Callable, Mapping, Sequence, Any

from . import learn
from .rl import registry as rl_registry

ToolFn = Callable[[], tuple[Mapping[str, float], Mapping[str, float]]]


def execute_plan(
    plans: Mapping[str, Sequence[ToolFn]],
    context: Mapping[str, Any],
    *,
    policy_registry: rl_registry.PolicyRegistry | None = None,
) -> list[Mapping[str, float]]:
    """Choose and execute a tool plan via reinforcement learning.

    Parameters
    ----------
    plans:
        Mapping from plan labels to sequences of tool callables.
    context:
        Features describing the current task. These are forwarded to the
        learning helper for bandit selection.
    policy_registry:
        Optional policy registry used for the ``tool_planning`` domain.

    Returns
    -------
    list of dict
        The list of outcomes produced by tools in the executed plan.
    """

    outputs: list[Mapping[str, float]] = []

    def act(label: str):
        nonlocal outputs
        outputs = []
        total_cost = 0.0
        total_latency = 0.0
        success = 1.0
        for tool in plans[label]:
            outcome, signals = tool()
            outputs.append(outcome)
            total_cost += float(outcome.get("cost_usd", 0.0))
            total_latency += float(outcome.get("latency_ms", 0.0))
            if signals.get("success", 1.0) <= 0.0:
                success = 0.0
        outcome = {"cost_usd": total_cost, "latency_ms": total_latency}
        signals = {"quality": success}
        return outcome, signals

    learn.learn(
        "tool_planning",
        context,
        list(plans.keys()),
        act,
        policy_registry=policy_registry,
    )
    return outputs

__all__ = ["execute_plan"]
