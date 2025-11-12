"""Compatibility shim for LearningEngine.

Historically, tests imported LearningEngine from `platform.core.learning_engine`.
The concrete implementation now lives under `platform.rl.learning_engine`.
This module re-exports the class to maintain backwards compatibility.
"""

from __future__ import annotations

from platform.rl.learning_engine import LearningEngine


__all__ = ["LearningEngine"]
