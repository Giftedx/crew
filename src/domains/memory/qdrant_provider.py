"""Deprecated Qdrant client factory provider.

This module is deprecated. Use src.domains.memory.vector.client_factory instead.
"""
import warnings
from domains.memory.vector.client_factory import get_qdrant_client as _get_qdrant_client_impl

warnings.warn(
    "src/domains/memory/qdrant_provider.py is deprecated. "
    "Use src/domains/memory/vector/client_factory.py instead.",
    DeprecationWarning,
    stacklevel=2,
)

get_qdrant_client = _get_qdrant_client_impl

__all__ = ["get_qdrant_client"]
