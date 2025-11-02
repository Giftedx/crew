"""Typed shim around crewai.tools.BaseTool with StepResult helpers.

crewai exposes an untyped ``BaseTool`` which propagates ``Any`` making subclass
checks noisy under mypy. We define a lightweight Protocol-compatible base class
that mirrors the minimal surface we rely upon to regain type safety for our
internal tools without modifying the third-party dependency.

This module also introduces :class:`StepResultHelperMixin`, giving tool authors
consistent factories for producing :class:`~ultimate_discord_intelligence_bot.step_result.StepResult`
instances and a convenience wrapper to normalize third-party results. The
helpers reduce boilerplate across tools while consolidating StepResult contract
usage in a single location.
"""
from __future__ import annotations
import contextlib
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar, runtime_checkable
if TYPE_CHECKING:
    from platform.core.step_result import ErrorContext, StepResult
from platform.core.step_result import StepResult

@runtime_checkable
class _BaseToolProto(Protocol):
    """Minimal protocol describing what we rely on from CrewAI tools.

    We intentionally keep the surface area small while still mirroring the
    commonly present ``name`` and ``description`` attributes from the vendor
    BaseTool so future upstream introspection (e.g. auto-documentation or
    selection UIs) does not break when interacting with our shimmed tools.
    """
    name: str | None
    description: str | None

    def run(self, *args: Any, **kwargs: Any) -> StepResult:
        ...
R_co = TypeVar('R_co', covariant=True)

class StepResultHelperMixin:
    """Utility helpers for tools producing :class:`StepResult` payloads.

    The mixin centralises success/error factory methods and exposes
    :meth:`ensure_step_result` to coerce arbitrary outputs (legacy dicts,
    ``None`` sentinels, etc.) into ``StepResult`` instances.
    """

    @staticmethod
    def result_ok(**data: Any) -> StepResult:
        """Return a successful ``StepResult`` with optional payload."""
        return StepResult.ok(**data)

    @staticmethod
    def result_skip(**data: Any) -> StepResult:
        """Return a skipped ``StepResult`` (treated as success for control flow)."""
        return StepResult.skip(**data)

    @staticmethod
    def result_uncertain(**data: Any) -> StepResult:
        """Return an ``uncertain`` ``StepResult`` for legacy tri-state flows."""
        return StepResult.uncertain(**data)

    @staticmethod
    def result_fail(error: str, *, error_category: Any | None=None, retryable: bool=False, context: ErrorContext | None=None, **data: Any) -> StepResult:
        """Return a failed ``StepResult`` with optional metadata."""
        return StepResult.fail(error=error, error_category=error_category, retryable=retryable, context=context, **data)

    @staticmethod
    def ensure_step_result(result: Any, *, context: ErrorContext | None=None) -> StepResult:
        """Coerce ``result`` into a :class:`StepResult`.

        Accepted inputs:

        * ``StepResult`` instances - returned unchanged.
        * ``Mapping`` values - interpreted using common conventions. When a
          ``status`` key is present the payload is routed through
          :meth:`StepResult.from_dict`. Dicts containing either ``success`` or
          ``error`` keys are converted into success/failure StepResults while
          preserving ancillary data and recognised metadata fields. Remaining
          mappings default to a successful result.
        * ``None`` - treated as ``StepResult.ok()`` for ergonomic optional
          returns.
        * All other objects - wrapped in ``StepResult.ok(result=obj)``.
        """
        if isinstance(result, StepResult):
            return result
        if isinstance(result, Mapping):
            payload = dict(result)
            if 'status' in payload:
                return StepResult.from_dict(payload, context=context)
            metadata = payload.pop('metadata', None)
            if payload.get('success') is True:
                payload.pop('success', None)
                step = StepResult.ok(**payload)
            elif payload.get('success') is False or 'error' in payload:
                error_message = payload.pop('error', 'Unknown error')
                payload.pop('success', None)
                fail_kwargs: dict[str, Any] = {'error_category': payload.pop('error_category', None), 'retryable': payload.pop('retryable', False), 'context': payload.pop('error_context', None) or context}
                step = StepResult.fail(error=str(error_message), **{k: v for k, v in fail_kwargs.items() if v is not None}, **payload)
            else:
                step = StepResult.ok(**payload)
            if metadata is not None:
                if not isinstance(metadata, dict):
                    metadata = {'value': metadata}
                step.metadata.update(metadata)
            return step
        if result is None:
            return StepResult.ok()
        return StepResult.ok(result=result)

class BaseTool(StepResultHelperMixin, Generic[R_co]):
    """Generic typed wrapper.

    Subclasses should type their internal ``_run``/``run`` returning structured
    dict payloads or domain objects.  The generic parameter ``R`` captures that
    return type for callers.
    """
    name: str | None = None
    description: str | None = None

    def run(self, *args: Any, **kwargs: Any) -> StepResult:
        """Concrete subclasses must implement.

        Body raises to make misuse explicit at runtime.
        """
        raise NotImplementedError('Subclasses must implement run()')

    def publish_message(self, msg_type: str, content: str, **metadata: Any) -> None:
        with contextlib.suppress(Exception):
            from platform.config.configuration import get_config
            config = get_config()
            if getattr(config, 'enable_agent_message_bus', False):
                from platform.rl.agent_messaging.redis_bus import AgentMessage, MessagePriority, MessageType
                type_mapping = {'note': MessageType.NOTE, 'evidence': MessageType.EVIDENCE, 'warning': MessageType.WARNING, 'ask': MessageType.REQUEST_INSIGHT, 'answer': MessageType.ANSWER}
                message_type = type_mapping.get(msg_type, MessageType.NOTE)
                from ultimate_discord_intelligence_bot.tenancy.context import current_tenant
                ctx = current_tenant()
                tenant_id = ctx.tenant_id if ctx else 'default'
                import asyncio
                from platform.rl.agent_messaging import AgentMessageBus
                try:
                    asyncio.get_running_loop()
                except RuntimeError:
                    return

                async def _publish():
                    bus = AgentMessageBus()
                    await bus.connect()
                    try:
                        message = AgentMessage(type=message_type, content=content, sender_agent_id=metadata.get('agent_id'), priority=MessagePriority.NORMAL, metadata=metadata)
                        await bus.publish(message, tenant_id=tenant_id)
                    finally:
                        await bus.disconnect()
                if not hasattr(self, '_background_tasks'):
                    self._background_tasks = []
                self._background_tasks.append(asyncio.create_task(_publish()))
                return
        with contextlib.suppress(Exception):
            from typing import cast
            from ultimate_discord_intelligence_bot.tenancy.shared_context import AgentMessage, MessageType, current_shared_context
            bus = current_shared_context()
            if bus is None:
                return
            valid_msg_type = msg_type if msg_type in {'note', 'ask', 'answer', 'evidence', 'warning'} else 'note'
            bus.publish(AgentMessage(type=cast('MessageType', valid_msg_type), content=content, metadata=metadata))

    def note(self, content: str, **metadata: Any) -> None:
        self.publish_message('note', content, **metadata)

    def evidence(self, content: str, **metadata: Any) -> None:
        self.publish_message('evidence', content, **metadata)
__all__ = ['BaseTool', 'StepResultHelperMixin']