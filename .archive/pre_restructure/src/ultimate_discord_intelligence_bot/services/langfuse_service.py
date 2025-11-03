from __future__ import annotations

import json
import logging
import os
from typing import Any

from core.settings import SecureConfig, get_settings

from obs import metrics
from ultimate_discord_intelligence_bot.step_result import ErrorCategory, ErrorContext, StepResult


logger = logging.getLogger(__name__)

try:
    from langfuse import Langfuse as _LangfuseClient  # type: ignore[import-not-found]
    from langfuse.model import CreateSpan, CreateTrace, UpdateSpan, UpdateTrace  # type: ignore[import-not-found]

    _LANGFUSE_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - optional dependency path
    _LangfuseClient = None  # type: ignore[assignment]
    CreateSpan = CreateTrace = UpdateSpan = UpdateTrace = None  # type: ignore[assignment]
    _LANGFUSE_IMPORT_ERROR = exc


def _sanitize(value: Any) -> Any:
    """Sanitize values for Langfuse payloads (best-effort)."""

    if isinstance(value, StepResult):
        return _sanitize(value.to_dict())
    if isinstance(value, dict):
        return {str(k): _sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_sanitize(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    try:
        json.dumps(value)
        return value
    except Exception:  # pragma: no cover - defensive
        return str(value)


class LangfuseService:
    """Feature-flagged Langfuse exporter that complies with ``StepResult`` semantics."""

    def __init__(self, settings: SecureConfig | None = None) -> None:
        self._settings = settings or get_settings()
        self.enabled = bool(getattr(self._settings, "enable_langfuse_export", False))
        self._client: Any | None = None
        self._import_error: Exception | None = _LANGFUSE_IMPORT_ERROR

        self.public_key = getattr(self._settings, "langfuse_public_key", None) or os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = getattr(self._settings, "langfuse_secret_key", None) or os.getenv("LANGFUSE_SECRET_KEY")
        self.base_url = getattr(self._settings, "langfuse_base_url", None) or os.getenv("LANGFUSE_BASE_URL")

        if not self.enabled:
            logger.debug("Langfuse export disabled via feature flag")
            return

        if _LangfuseClient is None or CreateTrace is None:
            logger.debug("Langfuse client unavailable: %s", self._import_error)
            self.enabled = False
            return

        if not self.public_key or not self.secret_key:
            logger.debug("Langfuse API keys missing; export disabled")
            self.enabled = False
            return

        client_kwargs: dict[str, Any] = {
            "public_key": self.public_key,
            "secret_key": self.secret_key,
        }
        if self.base_url:
            # Langfuse SDK accepts ``host`` for custom deployments. ``base_url`` retained for clarity.
            client_kwargs["host"] = self.base_url

        try:
            self._client = _LangfuseClient(**client_kwargs)
        except Exception as exc:  # pragma: no cover - optional dependency failure
            logger.warning("Failed to initialize Langfuse client: %s", exc)
            self._import_error = exc
            self.enabled = False

    # ---------------------------------------------------------------------
    # Trace helpers
    # ---------------------------------------------------------------------

    def create_trace(
        self,
        name: str,
        user_id: str,
        *,
        metadata: dict[str, Any] | None = None,
        input_data: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> StepResult:
        if not self._client or not self.enabled or CreateTrace is None:
            return StepResult.skip(reason="langfuse_disabled")

        metadata = _sanitize(metadata or {})
        input_payload = _sanitize(input_data or {})
        tags = tags or []

        try:
            trace = self._client.trace(
                CreateTrace(
                    name=name,
                    user_id=user_id,
                    metadata=metadata,
                    input=input_payload,
                    tags=tags,
                )
            )
            try:  # pragma: no cover - metrics optional
                metrics.LANGFUSE_TRACES.labels(**metrics.label_ctx(), status="success").inc()
            except Exception:
                logger.debug("Langfuse trace metric emit failed", exc_info=True)
            return StepResult.ok(trace=trace, trace_id=getattr(trace, "id", None))
        except Exception as exc:
            try:  # pragma: no cover - metrics optional
                metrics.LANGFUSE_TRACES.labels(**metrics.label_ctx(), status="error").inc()
            except Exception:
                logger.debug("Langfuse trace metric emit failed (error)", exc_info=True)
            return StepResult.with_context(
                success=False,
                error=f"Langfuse trace creation failed: {exc}",
                error_category=ErrorCategory.DEPENDENCY_FAILURE,
                context=ErrorContext(
                    operation="langfuse_trace", component="langfuse", tenant=user_id, workspace=user_id
                ),
            )

    def create_span(
        self,
        trace: Any,
        name: str,
        input_data: dict[str, Any],
        *,
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        if not self._client or not self.enabled or CreateSpan is None or trace is None:
            return StepResult.skip(reason="langfuse_disabled")

        metadata = _sanitize(metadata or {})
        input_payload = _sanitize(input_data)

        try:
            span = trace.span(CreateSpan(name=name, input=input_payload, metadata=metadata))
            try:  # pragma: no cover - metrics optional
                metrics.LANGFUSE_SPANS.labels(**metrics.label_ctx(), status="started").inc()
            except Exception:
                logger.debug("Langfuse span metric emit failed", exc_info=True)
            return StepResult.ok(span=span, span_name=name)
        except Exception as exc:
            try:  # pragma: no cover - metrics optional
                metrics.LANGFUSE_SPANS.labels(**metrics.label_ctx(), status="error").inc()
            except Exception:
                logger.debug("Langfuse span metric emit failed (error)", exc_info=True)
            return StepResult.with_context(
                success=False,
                error=f"Langfuse span creation failed: {exc}",
                error_category=ErrorCategory.DEPENDENCY_FAILURE,
                context=ErrorContext(operation="langfuse_span", component="langfuse", tenant=name, workspace=name),
            )

    def update_span(self, span: Any, output_data: dict[str, Any] | None = None, error: str | None = None) -> StepResult:
        if not self._client or not self.enabled or UpdateSpan is None or span is None:
            return StepResult.skip(reason="langfuse_disabled")

        output_payload = _sanitize(output_data or {})

        try:
            span.update(
                UpdateSpan(
                    output=output_payload,
                    level="ERROR" if error else "DEFAULT",
                    status_message=error,
                )
            )
            self.flush()
            try:  # pragma: no cover - metrics optional
                metrics.LANGFUSE_SPANS.labels(
                    **metrics.label_ctx(), status="completed" if not error else "errored"
                ).inc()
            except Exception:
                logger.debug("Langfuse span completion metric emit failed", exc_info=True)
            return StepResult.ok()
        except Exception as exc:
            try:  # pragma: no cover - metrics optional
                metrics.LANGFUSE_SPANS.labels(**metrics.label_ctx(), status="update_error").inc()
            except Exception:
                logger.debug("Langfuse span metric emit failed (update error)", exc_info=True)
            return StepResult.with_context(
                success=False,
                error=f"Langfuse span update failed: {exc}",
                error_category=ErrorCategory.DEPENDENCY_FAILURE,
                context=ErrorContext(operation="langfuse_span", component="langfuse"),
            )

    def finalize_trace(
        self,
        trace: Any,
        output_data: dict[str, Any] | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        if not self._client or not self.enabled or trace is None:
            return StepResult.skip(reason="langfuse_disabled")

        try:
            payload: dict[str, Any] = {
                "output": _sanitize(output_data or {}),
            }
            metadata_payload = _sanitize(metadata or {})
            if metadata_payload:
                payload["metadata"] = metadata_payload

            status = "ERROR" if error else "SUCCESS"
            payload["status"] = status
            if error:
                payload["status_message"] = error

            if UpdateTrace is not None:
                trace.update(UpdateTrace(**payload))
            else:  # pragma: no cover - legacy SDK fallback
                trace.update(**payload)
            self.flush()
            return StepResult.ok()
        except Exception as exc:
            return StepResult.with_context(
                success=False,
                error=f"Langfuse trace update failed: {exc}",
                error_category=ErrorCategory.DEPENDENCY_FAILURE,
                context=ErrorContext(operation="langfuse_trace", component="langfuse"),
            )

    def flush(self) -> None:
        if not self._client or not self.enabled:
            return
        try:
            self._client.flush()
        except Exception:  # pragma: no cover - best effort flush
            logger.debug("Langfuse flush failed", exc_info=True)


_LANGFUSE_SINGLETON: LangfuseService | None = None


def get_langfuse_service() -> LangfuseService:
    """Return a cached Langfuse service instance."""

    global _LANGFUSE_SINGLETON
    if _LANGFUSE_SINGLETON is None:
        _LANGFUSE_SINGLETON = LangfuseService()
    return _LANGFUSE_SINGLETON


__all__ = ["LangfuseService", "get_langfuse_service"]
