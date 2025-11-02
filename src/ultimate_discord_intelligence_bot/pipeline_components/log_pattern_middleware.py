"""Pipeline middleware that captures step logs and extracts recurring patterns."""

from __future__ import annotations

import contextlib
import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .middleware import BasePipelineStepMiddleware, StepContext


if TYPE_CHECKING:
    from collections.abc import Iterable
    from platform.core.step_result import StepResult


@dataclass
class _CapturedLog:
    """Lightweight representation of a log message used for summarisation."""

    created: float
    level: str
    logger_name: str
    message: str


class _PipelineLogCaptureHandler(logging.Handler):
    """Collects pipeline log records for pattern analysis."""

    def __init__(self, prefix: str, max_records: int, level: int) -> None:
        super().__init__(level=level)
        self._prefix = prefix
        self._max_records = max_records
        self._records: list[_CapturedLog] = []

    def emit(self, record: logging.LogRecord) -> None:
        if not record.name.startswith(self._prefix):
            return
        try:
            message = record.getMessage()
        except Exception:
            message = record.msg if isinstance(record.msg, str) else repr(record.msg)
        self._records.append(_CapturedLog(record.created, record.levelname, record.name, message))
        if len(self._records) > self._max_records:
            self._records.pop(0)

    def records(self) -> list[_CapturedLog]:
        return list(self._records)


class LogPatternMiddleware(BasePipelineStepMiddleware):
    """Attach per-step log summaries to :class:`StepResult.metadata`.

    The middleware briefly installs an in-memory log handler for the duration
    of each pipeline step. Once the step completes (successfully or with an
    error) the captured messages are collapsed into a small, structured
    summary that highlights dominant log patterns, grouped severities, and
    sample messages. This mirrors the "knowledge dense" telemetry requirement
    from our observability research, giving downstream agents immediate
    insight without replaying the full log stream.
    """

    _HANDLER_KEY = "log_patterns.handler"
    _LOGGER_KEY = "log_patterns.logger"
    _SUMMARY_KEY = "log_patterns.summary"

    def __init__(
        self,
        *,
        logger_prefix: str = "ultimate_discord_intelligence_bot",
        max_records: int = 250,
        max_patterns: int = 5,
        include_debug: bool = False,
    ) -> None:
        self._logger_prefix = logger_prefix
        self._max_records = max_records
        self._max_patterns = max_patterns
        self._level = logging.DEBUG if include_debug else logging.INFO

    async def before_step(self, context: StepContext) -> None:
        handler = _PipelineLogCaptureHandler(
            prefix=self._logger_prefix, max_records=self._max_records, level=self._level
        )
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        context.metadata[self._HANDLER_KEY] = handler
        context.metadata[self._LOGGER_KEY] = root_logger

    async def after_step(self, context: StepContext) -> None:
        handler = self._detach_handler(context)
        if handler is None:
            return
        summary = self._build_summary(handler.records())
        context.metadata[self._SUMMARY_KEY] = summary
        result = context.result
        if result is not None:
            self._attach_summary(result, summary)

    async def on_error(self, context: StepContext) -> None:
        handler = self._detach_handler(context)
        if handler is None:
            return
        summary = self._build_summary(handler.records())
        context.metadata[self._SUMMARY_KEY] = summary

    def _detach_handler(self, context: StepContext) -> _PipelineLogCaptureHandler | None:
        handler = context.metadata.pop(self._HANDLER_KEY, None)
        logger = context.metadata.pop(self._LOGGER_KEY, None)
        if handler is None or logger is None:
            return None
            with contextlib.suppress(Exception):
                logger.removeHandler(handler)
        return handler

    def _attach_summary(self, result: StepResult, summary: dict[str, Any]) -> None:
        observability = result.metadata.setdefault("observability", {})
        observability["log_patterns"] = summary

    def _build_summary(self, records: Iterable[_CapturedLog]) -> dict[str, Any]:
        records_list = list(records)
        if not records_list:
            return {"total_records": 0, "levels": {}, "sources": [], "top_patterns": [], "recent_errors": []}
        level_counter = Counter(rec.level for rec in records_list)
        unique_sources = sorted({rec.logger_name for rec in records_list})
        pattern_counter: Counter[str] = Counter()
        pattern_examples: dict[str, _CapturedLog] = {}
        pattern_levels: dict[str, set[str]] = defaultdict(set)
        for rec in records_list:
            pattern = self._normalise(rec.message)
            pattern_counter[pattern] += 1
            pattern_levels[pattern].add(rec.level)
            pattern_examples.setdefault(pattern, rec)
        top_patterns = []
        for pattern, count in pattern_counter.most_common(self._max_patterns):
            example = pattern_examples[pattern]
            top_patterns.append(
                {
                    "pattern": pattern,
                    "count": count,
                    "levels": sorted(pattern_levels[pattern]),
                    "example": example.message,
                }
            )
        recent_errors = [
            {"message": rec.message, "level": rec.level, "logger": rec.logger_name}
            for rec in records_list
            if rec.level in {"WARNING", "ERROR", "CRITICAL"}
        ][-5:]
        return {
            "total_records": len(records_list),
            "levels": dict(level_counter),
            "sources": unique_sources,
            "top_patterns": top_patterns,
            "recent_errors": recent_errors,
            "first_timestamp": records_list[0].created,
            "last_timestamp": records_list[-1].created,
        }

    @staticmethod
    def _normalise(message: str) -> str:
        """Collapse dynamic tokens to reveal structural log patterns."""
        message = message.strip().lower()
        message = _TOKEN_RE.sub(" <num> ", message)
        message = _HEX_RE.sub(" <hex> ", message)
        message = re.sub("\\s+", " ", message)
        return message.strip()


_TOKEN_RE = re.compile("\\b\\d+(?:\\.\\d+)?\\b")
_HEX_RE = re.compile("0x[0-9a-f]+", re.IGNORECASE)
__all__ = ["LogPatternMiddleware"]
