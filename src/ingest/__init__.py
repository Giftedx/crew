"""Compatibility shim for ingest package.

Expose a lightweight local ``pipeline`` module that mirrors the legacy import
path (``from ingest import pipeline``) used by tests, while keeping the heavy
domain pipeline available elsewhere.
"""

from . import pipeline


__all__ = ["pipeline"]
