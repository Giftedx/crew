"""
Data models for Creator Operations.

This module contains SQLAlchemy models for the creator operations system,
including cross-platform content, accounts, interactions, and analysis results.
"""

from __future__ import annotations


__all__ = [
    "Account",
    "BaseModel",
    "Claim",
    "Embedding",
    "Interaction",
    "Media",
    "Person",
    "Topic",
    "Unit",
]

from .schema import (
    Account,
    BaseModel,
    Media,
    Unit,
)


# Temporary placeholder classes for missing models
class Claim:
    pass


class Embedding:
    pass


class Interaction:
    pass


class Person:
    pass


class Topic:
    pass
