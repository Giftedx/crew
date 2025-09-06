"""Request-scoped cumulative cost tracking.

Provides a lightweight thread-local tracker recording total spend and per-task
spend for all LLM calls within a higher-level pipeline request.  Intended to
augment the existing *per-request* single-call ceiling enforced by
``TokenMeter`` / tenant config with cumulative enforcement across multiple
model invocations in a single pipeline execution.

Example
-------

from services.request_budget import track_request_budget, current_request_tracker

with track_request_budget(total_limit=1.50, per_task_limits={"analysis": 0.75}):
    # First model call (0.40 USD) -> OK
    # Second analysis call (0.50 USD) -> OK cumulative 0.90, analysis 0.90 > 0.75 -> rejected

Design Notes
------------
- Thread-local storage keeps implementation simple for current synchronous
  pipeline execution model. If the pipeline becomes multi-threaded per request
  we may need a contextvars based approach.
- Silent no-op when no context is active so callers can unconditionally attempt
  to record spend.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass, field

__all__ = [
    "RequestCostTracker",
    "track_request_budget",
    "current_request_tracker",
]

_thread_local = threading.local()


@dataclass
class RequestCostTracker:
    total_limit: float | None = None
    per_task_limits: dict[str, float] = field(default_factory=dict)
    total_spent: float = 0.0
    per_task_spent: dict[str, float] = field(default_factory=dict)

    def can_charge(self, amount: float, task: str) -> bool:
        new_total = self.total_spent + amount
        if self.total_limit is not None and new_total > self.total_limit:
            return False
        if task:
            limit = self.per_task_limits.get(task)
            if limit is not None and self.per_task_spent.get(task, 0.0) + amount > limit:
                return False
        return True

    def charge(self, amount: float, task: str) -> None:
        if amount < 0:
            return
        self.total_spent += amount
        if task:
            self.per_task_spent[task] = self.per_task_spent.get(task, 0.0) + amount


@contextmanager
def track_request_budget(total_limit: float | None, per_task_limits: dict[str, float] | None = None):
    prev = getattr(_thread_local, "req_budget", None)
    tracker = RequestCostTracker(total_limit=total_limit, per_task_limits=per_task_limits or {})
    _thread_local.req_budget = tracker
    try:
        yield tracker
    finally:
        _thread_local.req_budget = prev


def current_request_tracker() -> RequestCostTracker | None:
    return getattr(_thread_local, "req_budget", None)
