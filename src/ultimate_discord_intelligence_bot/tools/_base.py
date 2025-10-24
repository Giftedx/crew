"""Typed shim around crewai.tools.BaseTool.

crewai exposes an untyped ``BaseTool`` which propagates ``Any`` making subclass
checks noisy under mypy. We define a lightweight Protocol-compatible base
class that mirrors the minimal surface we rely upon to regain type safety for
our internal tools without modifying the third-party dependency.
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Protocol,
    TypeVar,
    runtime_checkable,
)


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.step_result import StepResult


@runtime_checkable
class _BaseToolProto(Protocol):
    """Minimal protocol describing what we rely on from CrewAI tools.

    We intentionally keep the surface area small while still mirroring the
    commonly present ``name`` and ``description`` attributes from the vendor
    BaseTool so future upstream introspection (e.g. auto‑documentation or
    selection UIs) does not break when interacting with our shimmed tools.
    """

    name: str | None  # optional in our internal tools
    description: str | None

    def run(self, *args: Any, **kwargs: Any) -> StepResult:  # minimal execution surface
        ...  # pragma: no cover


R_co = TypeVar("R_co", covariant=True)


class BaseTool(Generic[R_co]):
    """Generic typed wrapper.

    Subclasses should type their internal ``_run``/``run`` returning structured
    dict payloads or domain objects.  The generic parameter ``R`` captures that
    return type for callers.
    """

    # Common metadata attributes used by our tools
    name: str | None = None
    description: str | None = None

    # We don't add new behaviour—purely for typing.
    def run(self, *args: Any, **kwargs: Any) -> StepResult:  # runtime provided by subclass
        """Concrete subclasses must implement.

        Body raises to make misuse explicit at runtime.
        """
        raise NotImplementedError("Subclasses must implement run()")

    # ---------------------- Optional agent-comms helpers ----------------------
    # Tools may call these to publish lightweight messages to the shared
    # agent communication bus when present. No hard dependency is introduced
    # and absence of the bus is silently ignored.
    def publish_message(self, msg_type: str, content: str, **metadata: Any) -> None:
        try:
            from typing import cast

            from ultimate_discord_intelligence_bot.tenancy.shared_context import (
                AgentMessage,
                MessageType,
                current_shared_context,
            )

            bus = current_shared_context()
            if bus is None:
                return
            # Validate msg_type is a valid MessageType
            valid_msg_type = msg_type if msg_type in {"note", "ask", "answer", "evidence", "warning"} else "note"
            bus.publish(AgentMessage(type=cast("MessageType", valid_msg_type), content=content, metadata=metadata))
        except Exception:
            # Publishing is best-effort; never fail tool execution for bus issues
            return

    def note(self, content: str, **metadata: Any) -> None:
        self.publish_message("note", content, **metadata)

    def evidence(self, content: str, **metadata: Any) -> None:
        self.publish_message("evidence", content, **metadata)


__all__ = ["BaseTool"]
