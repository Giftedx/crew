from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Literal

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, current_tenant

MessageType = Literal["note", "ask", "answer", "evidence", "warning"]


@dataclass
class AgentMessage:
    """A simple message exchanged between agents during a crew run."""

    type: MessageType
    content: str
    timestamp: float = field(default_factory=lambda: time.time())
    from_agent: str | None = None
    to_agent: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SharedContext:
    """Shared context bus for agents within a single execution session.

    The bus is tenant-aware (labels only; no tenant text stored in metrics) and
    maintains an in-memory bounded history suitable for intra-process runs.
    """

    def __init__(self, session_id: str, max_messages: int = 1000) -> None:
        self.session_id = session_id
        self.max_messages = max_messages
        self._messages: list[AgentMessage] = []
        self._lock = threading.Lock()
        self._metrics = get_metrics()

    def publish(self, message: AgentMessage) -> None:
        """Publish a message to the bus (non-blocking)."""
        with self._lock:
            self._messages.append(message)
            # trim buffer if needed (keep last max_messages)
            if len(self._messages) > self.max_messages:
                overflow = len(self._messages) - self.max_messages
                del self._messages[0:overflow]
        # low-cardinality metrics: type only
        try:
            self._metrics.counter("agent_comms_messages_total", labels={"type": message.type}).inc()
        except Exception:
            # metrics are best-effort
            pass

    def history(self, msg_type: MessageType | None = None) -> list[AgentMessage]:
        """Return a snapshot of messages, optionally filtered by type."""
        with self._lock:
            if msg_type is None:
                return list(self._messages)
            return [m for m in self._messages if m.type == msg_type]


_thread_local = threading.local()


def with_shared_context(session_id: str, *, max_messages: int = 1000) -> SharedContext:
    """Create and set a shared context for the current thread.

    Returns the created shared context instance for direct use. Callers do not
    get an automatic context manager here to keep usage simple alongside
    existing crew lifecycle management. Clearing can be done via
    ``clear_shared_context``.
    """

    ctx = SharedContext(session_id=session_id, max_messages=max_messages)
    setattr(_thread_local, "shared_ctx", ctx)
    return ctx


def clear_shared_context() -> None:
    """Remove the shared context from the current thread if present."""
    try:
        delattr(_thread_local, "shared_ctx")
    except Exception:
        pass


def current_shared_context() -> SharedContext | None:
    """Return the current thread's shared context if set."""
    return getattr(_thread_local, "shared_ctx", None)


def tenant_labels() -> dict[str, str]:
    """Low-cardinality tenant label helper for external metrics.

    Intentionally returns only IDs and avoids verbose labels.
    """
    t: TenantContext | None = current_tenant()
    if not t:
        return {"tenant": "unknown", "workspace": "unknown"}
    return {"tenant": t.tenant_id or "unknown", "workspace": t.workspace_id or "unknown"}


__all__ = [
    "MessageType",
    "AgentMessage",
    "SharedContext",
    "with_shared_context",
    "clear_shared_context",
    "current_shared_context",
    "tenant_labels",
]
