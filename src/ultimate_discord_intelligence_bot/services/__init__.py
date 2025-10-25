"""Shared services for prompt engineering, routing and learning.

This package uses lazy imports to avoid importing heavy optional dependencies
at module import time (e.g., openai). Accessing an attribute will import the
corresponding submodule on demand.
"""

from __future__ import annotations

from importlib import import_module


_MAPPING = {
    # Module re-export for monkeypatch compatibility
    "openrouter_service": (".openrouter_service", None),  # return module
    "memory_service": (".memory_service", None),  # return module for patch targets
    "prompt_engine": (".prompt_engine", None),  # return module for patch targets
    # Classes / callables
    "LLMCache": (".cache", "LLMCache"),
    "EvaluationHarness": (".evaluation_harness", "EvaluationHarness"),
    "LearningEngine": (".learning_engine", "LearningEngine"),
    "AnalyticsStore": (".logging_utils", "AnalyticsStore"),
    "MemoryMaintenance": (".maintenance", "MemoryMaintenance"),
    "MemoryService": (".memory_service", "MemoryService"),
    "OpenRouterService": (".openrouter_service", "OpenRouterService"),
    "ContentPoller": (".poller", "ContentPoller"),
    "PromptEngine": (".prompt_engine", "PromptEngine"),
    "TokenMeter": (".token_meter", "TokenMeter"),
}


__all__ = list(_MAPPING.keys())


def __getattr__(name: str):  # pragma: no cover - thin lazy loader
    mod_info = _MAPPING.get(name)
    if not mod_info:
        raise AttributeError(name)
    mod_path, attr = mod_info
    module = import_module(f"{__name__}{mod_path}")
    if attr is None:
        return module
    try:
        return getattr(module, name if attr is True else attr)
    except AttributeError as exc:
        raise AttributeError(name) from exc
