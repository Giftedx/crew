"""Compatibility shim for logfire_spans in ultimate_discord_intelligence_bot.obs

This module re-exports the logfire_spans API from platform.observability.logfire_spans
to preserve the historical import path.
"""

from platform.observability.logfire_spans import is_logfire_enabled, set_span_attribute, span, with_span_async


__all__ = ["is_logfire_enabled", "set_span_attribute", "span", "with_span_async"]
