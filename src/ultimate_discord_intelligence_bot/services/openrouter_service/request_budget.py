"""Request budget tracking for OpenRouter service."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field


@dataclass
class RequestTracker:
    """Tracks request budget and costs."""

    max_cost: float
    current_cost: float = 0.0
    task_costs: dict[str, float] = field(default_factory=dict)

    def can_charge(self, cost: float, task_type: str) -> bool:
        """Check if we can charge the given cost."""
        return (self.current_cost + cost) <= self.max_cost

    def charge(self, cost: float, task_type: str) -> None:
        """Charge the given cost."""
        self.current_cost += cost
        if self.task_costs is not None:
            self.task_costs[task_type] = self.task_costs.get(task_type, 0.0) + cost


# Thread-local storage for request tracker
_thread_local = threading.local()


def current_request_tracker() -> RequestTracker | None:
    """Get current request tracker from thread-local storage."""
    return getattr(_thread_local, "tracker", None)


def set_request_tracker(tracker: RequestTracker) -> None:
    """Set request tracker in thread-local storage."""
    _thread_local.tracker = tracker


def clear_request_tracker() -> None:
    """Clear request tracker from thread-local storage."""
    if hasattr(_thread_local, "tracker"):
        delattr(_thread_local, "tracker")
