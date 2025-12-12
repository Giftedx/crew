"""Test refactoring of memory subsystem."""
import sys
import pytest
from domains.memory.vector.client_factory import get_qdrant_client as new_get_client
from domains.memory.vector.client_factory import _DummyClient as NewDummyClient

def test_new_factory_import():
    """Verify the new factory can be imported and works."""
    client = new_get_client()
    assert client is not None

def test_deprecated_import_warning():
    """Verify importing from deprecated module raises warning."""
    # Ensure module is re-imported to trigger warning
    if 'domains.memory.qdrant_provider' in sys.modules:
        del sys.modules['domains.memory.qdrant_provider']

    with pytest.warns(DeprecationWarning, match="This module is deprecated"):
        from domains.memory.qdrant_provider import get_qdrant_client as old_get_client

    client_old = old_get_client()
    client_new = new_get_client()

    # Since get_qdrant_client uses lru_cache, they should be the same instance
    assert client_old is client_new

def test_deprecated_dummy_client_export():
    """Verify _DummyClient is exported from deprecated module."""
    # Ensure module is re-imported to trigger warning
    if 'domains.memory.qdrant_provider' in sys.modules:
        del sys.modules['domains.memory.qdrant_provider']

    with pytest.warns(DeprecationWarning):
        from domains.memory.qdrant_provider import _DummyClient

    assert _DummyClient is NewDummyClient
