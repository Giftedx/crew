from __future__ import annotations

"""
Proxy submodule for fastapi.testclient that forwards to the real FastAPI package.
"""

from pathlib import Path
import importlib
import os
import sys


def _import_real_fastapi_testclient():
    src_dir = str(Path(__file__).resolve().parents[1])  # /home/crew/src
    removed = []
    for p in list(sys.path):
        try:
            if os.path.abspath(p) == src_dir:
                removed.append(p)
                sys.path.remove(p)
        except Exception:
            continue
    try:
        return importlib.import_module("fastapi.testclient")
    finally:
        for p in removed:
            sys.path.insert(0, p)


try:
    _real = _import_real_fastapi_testclient()
    TestClient = _real.TestClient
    __all__ = ["TestClient"]
except Exception:
    # Fallback: Minimal placeholder to satisfy rare imports in tests
    class TestClient:  # pragma: no cover - placeholder
        def __init__(self, app) -> None:
            self.app = app

    __all__ = ["TestClient"]
