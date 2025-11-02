"""Dependency groups for organizing related dependencies."""

from __future__ import annotations

from .ai_ml import AI_ML_GROUP
from .cache import CACHE_GROUP
from .database import DATABASE_GROUP
from .monitoring import MONITORING_GROUP
from .vector import VECTOR_GROUP


__all__ = [
    "AI_ML_GROUP",
    "CACHE_GROUP",
    "DATABASE_GROUP",
    "MONITORING_GROUP",
    "VECTOR_GROUP",
]
