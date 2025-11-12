"""Shim module re-exporting the canonical MemoryStore and related types.

Tests historically import ``from memory.store import MemoryStore``. The
implementation lives under ``domains.memory.store``; this module forwards
those definitions for compatibility without duplicating logic.
"""

from __future__ import annotations

from domains.memory.store import MemoryItem, MemoryStore, RetentionPolicy


__all__ = ["MemoryItem", "MemoryStore", "RetentionPolicy"]
