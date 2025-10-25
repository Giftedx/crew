"""Root-level pytest configuration for this repo.

We enable asyncio support explicitly when the optional dependency is present.
In CI or minimal environments where pytest-asyncio isn't installed, tests that
don't require asyncio can still run by skipping the plugin.
"""

try:  # Optional: only enable if available
    import pytest_asyncio  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover - environment dependent
    pytest_plugins: list[str] = []
else:
    pytest_plugins = ["pytest_asyncio"]
