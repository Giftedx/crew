"""Middleware shim utilities for the minimal FastAPI stub.

This repository vendors a trimmed-down FastAPI-like interface (no Starlette).
To support stacking middlewares similarly to ``app.add_middleware`` we patch
the stub at runtime. TestClient is also adapted to execute the stacked chain.

Production environments using the real FastAPI should bypass this shim since
``FastAPI`` already supplies ``add_middleware`` semantics. The guards below
only apply when the attribute is missing.
"""

from __future__ import annotations

# Ensure mypy sees this module only once under server.middleware_shim
__all__ = ["install_middleware_support"]

import asyncio
from collections.abc import Callable
from typing import Any

try:
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient
except Exception:  # pragma: no cover - fastapi shim always importable in tests
    raise


def install_middleware_support() -> None:
    """Install add_middleware & execution chain if absent.

    Idempotent: safe to call multiple times.
    """

    patched_app = False
    if not hasattr(FastAPI, "add_middleware"):

        def add_middleware(self: Any, mw_cls: Any, **options: Any) -> None:
            chain = getattr(self, "_http_middlewares", [])
            instance = mw_cls(self, **options)
            # Prepend so rate limiter (typically first) executes before later additions
            chain.insert(0, instance)
            self._http_middlewares = chain

            def middleware(_type: str):  # noqa: D401
                def dec(fn: Callable[[Request], Any]):
                    self._http_middlewares.append(fn)
                    return fn

                return dec

            self.middleware = middleware

        FastAPI.add_middleware = add_middleware  # type: ignore[attr-defined]
        patched_app = True

    # If we didn't patch the FastAPI app (i.e., running real FastAPI), skip TestClient patching entirely
    if not patched_app:
        return
    # Patch TestClient only once
    if getattr(TestClient, "_patched_for_chain", False):  # pragma: no cover - idempotency guard
        return

    original_request = getattr(TestClient, "_request", None) or getattr(TestClient, "request")

    def _patched_request(self: Any, method: str, path: str, **kw: Any):
        app = self.app
        # If no chain, fall back
        chain = [mw for mw in getattr(app, "_http_middlewares", [])]
        if not chain:
            return original_request(self, method, path, **kw)

        async def terminal(req: Request):  # noqa: D401
            return original_request(self, method, path, **kw)

        async def invoke(i: int, req: Request):
            if i >= len(chain):
                return await terminal(req)
            current = chain[i]

            async def _call_next(r: Request):
                return await invoke(i + 1, r)

            # Support both class instances with .dispatch and simple callables
            if hasattr(current, "dispatch"):
                result = current.dispatch(req, _call_next)
            else:
                result = current(req, _call_next)
            if hasattr(result, "__await__"):
                result = await result
            return result

        req = Request(method=method.upper(), path=path)
        return asyncio.run(invoke(0, req))

    TestClient._request = _patched_request
    TestClient._patched_for_chain = True  # type: ignore[attr-defined]


__all__ = ["install_middleware_support"]
