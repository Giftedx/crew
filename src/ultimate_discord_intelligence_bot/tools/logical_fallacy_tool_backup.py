"""DEPRECATED MODULE.

This module used to contain a backup implementation of a logical fallacy
detector tool. It has been intentionally stripped to avoid duplicate class
definitions and to reduce type checking noise. All functionality now lives in
``logical_fallacy_tool.py``.

Any import of this module should be removed. Keeping the file (empty) for one
transition release only; it will be deleted in a subsequent cleanup pass.
"""

from __future__ import annotations

__all__: list[str] = []  # Nothing exported

DEPRECATION_NOTICE = (
    "logical_fallacy_tool_backup is deprecated; use logical_fallacy_tool instead"
)

def __getattr__(name: str):  # pragma: no cover - defensive guard
    raise AttributeError(DEPRECATION_NOTICE)

