"""Lazy loading system for tools and optional dependencies.

This module provides lazy loading capabilities to reduce memory footprint
and improve startup performance by deferring imports until actually needed.
"""

from .dependency_manager import DependencyManager
from .import_cache import ImportCache
from .tool_loader import LazyToolLoader


__all__ = [
    "DependencyManager",
    "ImportCache",
    "LazyToolLoader",
]
