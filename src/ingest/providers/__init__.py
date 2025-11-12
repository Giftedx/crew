"""Compatibility shim for ``ingest.providers``.

This package exposes provider-specific modules like ``ingest.providers.youtube``
that tests can import and monkeypatch. Avoid importing optional providers at
package import time to keep test environments lightweight.
"""

__all__: list[str] = []
