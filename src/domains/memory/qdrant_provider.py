"""Deprecated: Use src/domains/memory/vector/client_factory.py instead."""
import warnings
from domains.memory.vector.client_factory import get_qdrant_client, _DummyClient

warnings.warn(
    "This module is deprecated. Use domains.memory.vector.client_factory instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["get_qdrant_client", "_DummyClient"]
