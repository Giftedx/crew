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
    "get_lazy_loader",
]


def get_lazy_loader() -> LazyToolLoader:
    """Factory for a default LazyToolLoader instance.

    Provided for compatibility with fast tests expecting a simple accessor.
    """
    return LazyToolLoader()
