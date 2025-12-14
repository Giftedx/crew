"""Deprecated: Use src/domains/memory/vector/client_factory.py instead."""

import warnings

from domains.memory.vector.client_factory import _DummyClient, get_qdrant_client


warnings.warn(
    "This module is deprecated. Use domains.memory.vector.client_factory instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["_DummyClient", "get_qdrant_client"]
