"""Compatibility shims for legacy imports.

This lightweight package provides backward-compatible import paths for
older tests that expect a top-level ``memory`` package. The actual
implementations now live under ``ultimate_discord_intelligence_bot.memory``
and ``domains.memory``.

We re-export the public APIs needed by tests to avoid import errors
without duplicating implementations.
"""

# ruff: noqa: I001  # allow dynamic import block structure in this compatibility module

from __future__ import annotations

# Re-export VectorStore utilities from the canonical package
import importlib

try:  # Prefer the main app namespace
    _vs = importlib.import_module("ultimate_discord_intelligence_bot.memory.vector_store")
except Exception:  # Fallback to domains shim if present
    _vs = importlib.import_module("domains.memory.vector_store")

VectorRecord = _vs.VectorRecord
VectorStore = _vs.VectorStore

__all__ = [
    "VectorRecord",
    "VectorStore",
]
