"""Observability package (lightweight).

Avoid eager submodule imports to keep ``import obs.metrics`` cheap and free of
optional dependencies during tests. Import submodules explicitly where needed.
"""

__all__ = ["tracing", "metrics", "logging", "slo", "incident"]
