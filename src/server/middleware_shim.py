"""Middleware shim utilities for the minimal FastAPI stub.

This repository vendors a trimmed-down FastAPI-like interface (no Starlette).
To support stacking middlewares similarly to ``app.add_middleware`` we patch
the stub at runtime. TestClient is also adapted to execute the stacked chain.

Production environments using the real FastAPI should bypass this shim since
``FastAPI`` already supplies ``add_middleware`` semantics. The guards below
only apply when the attribute is missing.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

try:
    from fastapi import FastAPI, Request  # type: ignore
    from fastapi.testclient import TestClient  # type: ignore
except Exception:  # pragma: no cover - fastapi shim always importable in tests
    raise


def install_middleware_support() -> None:
    """Install add_middleware & execution chain if absent.

    Idempotent: safe to call multiple times.
    """

    if not hasattr(FastAPI, "add_middleware"):

        def add_middleware(self: Any, mw_cls: Any, **options: Any) -> None:  # type: ignore[no-untyped-def]
            chain = getattr(self, "_http_middlewares", [])
            instance = mw_cls(self, **options)
            # Prepend so rate limiter (typically first) executes before later additions
            chain.insert(0, instance)
            self._http_middlewares = chain

            def middleware(_type: str):  # noqa: D401
                def dec(fn: Callable):  # type: ignore[no-untyped-def]
                    self._http_middlewares.append(fn)
                    return fn

                return dec

            self.middleware = middleware  # type: ignore[attr-defined]

        FastAPI.add_middleware = add_middleware  # type: ignore[attr-defined]

    # Patch TestClient only once
    if getattr(TestClient, "_patched_for_chain", False):  # pragma: no cover - idempotency guard
        return

    original_request = TestClient._request

    def _patched_request(self: Any, method: str, path: str, **kw: Any):  # type: ignore[no-untyped-def]
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

        req = Request(method=method.upper(), path=path)  # type: ignore[call-arg]
        return asyncio.run(invoke(0, req))

    TestClient._request = _patched_request  # type: ignore
    TestClient._patched_for_chain = True  # type: ignore[attr-defined]


__all__ = ["install_middleware_support"]
