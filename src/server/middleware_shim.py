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
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, cast


try:  # pragma: no cover - fastapi shim always importable in tests
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient
except Exception:  # pragma: no cover
    raise


class MiddlewareLike(Protocol):  # pragma: no cover - structural typing only
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Any]]) -> Any: ...


# A middleware entry can be either an object with a dispatch method OR a 2-arg callable
MiddlewareEntry = MiddlewareLike | Callable[[Request, Callable[[Request], Awaitable[Any]]], Awaitable[Any] | Any]


def install_middleware_support() -> None:
    """Install add_middleware & execution chain if absent.

    Idempotent: safe to call multiple times.
    """

    if not hasattr(FastAPI, "add_middleware"):

        def _shim_add_middleware(self: Any, mw_cls: Any, **options: Any) -> None:
            chain: list[MiddlewareEntry] = list(getattr(self, "_http_middlewares", []))
            instance = mw_cls(self, **options)
            # Append so that earlier added (decorator) middlewares run before later class middlewares,
            # mimicking FastAPI's stacking order. This allows path/bypass flags set in early
            # function middlewares to be visible to downstream class-based middleware like the rate limiter.
            chain.append(cast("MiddlewareEntry", instance))
            self._http_middlewares = chain

            def middleware(_type: str):
                def decorator(fn: Callable[[Request], Any]):
                    async def two_arg(req: Request, _next: Callable[[Request], Awaitable[Any]]):
                        return fn(req)

                    chain.append(cast("MiddlewareEntry", two_arg))
                    self._http_middlewares = chain
                    return fn

                return decorator

            # attach 'middleware' helper if absent
            if not hasattr(self, "middleware"):
                self.middleware = middleware

        FastAPI.add_middleware = _shim_add_middleware

        # Also attach a class-level middleware helper so function middlewares can be
        # registered even before any add_middleware call occurs.
        if not hasattr(FastAPI, "middleware"):

            def _shim_middleware(self: Any, _type: str):
                def decorator(fn: Callable[[Request], Any]):
                    chain: list[MiddlewareEntry] = list(getattr(self, "_http_middlewares", []))

                    async def two_arg(req: Request, _next: Callable[[Request], Awaitable[Any]]):
                        return fn(req)

                    chain.append(two_arg)
                    self._http_middlewares = chain
                    return fn

                return decorator

            FastAPI.middleware = _shim_middleware
    # Patch TestClient only once (even with real FastAPI) so that, when a custom chain
    # is present on the app (via function middlewares), tests execute through it.
    if getattr(TestClient, "_patched_for_chain", False):  # pragma: no cover - idempotency guard
        return

    original_request = getattr(TestClient, "_request", None) or TestClient.request

    def _patched_request(self: Any, method: str, path: str, **kw: Any):
        app = self.app
        chain: list[MiddlewareEntry] = list(getattr(app, "_http_middlewares", []))
        if not chain:
            return original_request(self, method, path, **kw)

        async def terminal(req: Request):
            # Propagate potential alterations performed by middleware before delegating
            overridden_method = getattr(req, "method", method).upper()
            overridden_path = getattr(req, "url", None)
            if overridden_path is not None:
                overridden_path = getattr(req.url, "path", path)
            else:
                overridden_path = getattr(getattr(req, "scope", {}), "get", lambda *_: path)("path")
            request_kwargs = dict(kw)
            try:
                request_kwargs["headers"] = dict(req.headers)
            except Exception:
                request_kwargs["headers"] = kw.get("headers", {})
            query_bytes = getattr(getattr(req, "scope", {}), "get", lambda *_: b"")("query_string")
            if query_bytes:
                request_kwargs["params"] = query_bytes.decode("latin-1")
            return original_request(self, overridden_method, overridden_path or path, **request_kwargs)

        async def invoke(i: int, req: Request):
            if i >= len(chain):
                return await terminal(req)
            current = chain[i]

            async def _call_next(r: Request) -> Any:
                return await invoke(i + 1, r)

            # Support both class instances with .dispatch and simple callables
            if hasattr(current, "dispatch"):
                result = cast("MiddlewareLike", current).dispatch(req, _call_next)
            else:
                two_arg = cast(
                    "Callable[[Request, Callable[[Request], Awaitable[Any]]], Any]",
                    current,
                )
                result = two_arg(req, _call_next)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        # Minimal ASGI scope for Request construction (method/path only)
        # Normalize headers from kwargs into ASGI-style bytes tuples
        raw_headers: list[tuple[bytes, bytes]] = []
        try:
            hdrs = kw.get("headers") or {}
            if hasattr(hdrs, "items"):
                raw_headers = [(str(k).lower().encode("latin-1"), str(v).encode("latin-1")) for k, v in hdrs.items()]
        except Exception:
            raw_headers = []

        scope = {
            "type": "http",
            "method": method.upper(),
            "path": path,
            "headers": raw_headers,
            "query_string": b"",
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
            "scheme": "http",
            "root_path": "",
            "http_version": "1.1",
        }

        # Starlette style Request expects scope + receive; build a minimal receive callable.
        async def _dummy_receive():  # type: ignore[return-value]
            return {"type": "http.request", "body": b"", "more_body": False}

        try:
            req = Request(scope, receive=_dummy_receive)  # type: ignore[arg-type]
            if isinstance(getattr(req, "scope", None), dict):  # augment for limiter path lookup
                req.scope.setdefault("path", path)
        except TypeError:  # shim path
            try:  # pragma: no cover - defensive
                req = Request(method=method.upper(), path=path, headers={}, body=b"", query="")  # type: ignore[call-arg]
                if not hasattr(req, "scope"):
                    req.scope = {"path": path}
                else:
                    req.scope.setdefault("path", path)
            except Exception:  # fallback last resort
                req = Request(scope)  # type: ignore[call-arg]

        # Ensure the middleware chain returns a FastAPI Response
        return asyncio.run(invoke(0, req))

    # Patch both public and private entry points to be safe across client variants
    TestClient._request = _patched_request  # type: ignore[attr-defined]
    TestClient.request = _patched_request  # type: ignore[assignment]
    TestClient._patched_for_chain = True  # type: ignore[attr-defined]


__all__ = ["install_middleware_support"]
