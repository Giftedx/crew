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
    BaseTool so future upstream introspection (e.g. auto-documentation or
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
        # Try Redis-backed message bus first (if enabled)
        try:
            from core.secure_config import get_config

            config = get_config()
            if getattr(config, "enable_agent_message_bus", False):
                from ai.agent_messaging.redis_bus import AgentMessage, MessagePriority, MessageType

                # Map legacy types to new enum
                type_mapping = {
                    "note": MessageType.NOTE,
                    "evidence": MessageType.EVIDENCE,
                    "warning": MessageType.WARNING,
                    "ask": MessageType.REQUEST_INSIGHT,
                    "answer": MessageType.ANSWER,
                }

                message_type = type_mapping.get(msg_type, MessageType.NOTE)

                # Get tenant context
                from ultimate_discord_intelligence_bot.tenancy.context import current_tenant

                ctx = current_tenant()
                tenant_id = ctx.tenant_id if ctx else "default"

                # Create and publish message asynchronously
                import asyncio

                from ai.agent_messaging import AgentMessageBus

                # Get or create event loop
                try:
                    asyncio.get_running_loop()
                except RuntimeError:
                    # No running loop, skip async publish
                    return

                # Create message bus and publish (fire-and-forget)
                async def _publish():
                    bus = AgentMessageBus()
                    await bus.connect()
                    try:
                        message = AgentMessage(
                            type=message_type,
                            content=content,
                            sender_agent_id=metadata.get("agent_id"),
                            priority=MessagePriority.NORMAL,
                            metadata=metadata,
                        )
                        await bus.publish(message, tenant_id=tenant_id)
                    finally:
                        await bus.disconnect()

                # Keep a reference to avoid task being garbage-collected
                if not hasattr(self, "_background_tasks"):
                    self._background_tasks = []  # type: ignore[attr-defined]
                self._background_tasks.append(asyncio.create_task(_publish()))  # type: ignore[attr-defined]
                return
        except Exception:
            pass  # Fall back to legacy bus

        # Fall back to legacy in-memory bus
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
