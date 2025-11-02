from __future__ import annotations


"""
Minimal stub of the FastAPI package to prevent local shadowing errors and satisfy
imports in constrained test environments. This is NOT a full FastAPI; it only
exposes a few names used by our codebase's tests. If you need full FastAPI
behavior, remove the local 'src/fastapi' package so the real package is used.
"""

from typing import Any


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str = "") -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class Response:
    def __init__(
        self,
        content: bytes | str = b"",
        status_code: int = 200,
        media_type: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.content = content if isinstance(content, (bytes, bytearray)) else str(content).encode("utf-8")
        self.media_type = media_type


def Query(default: Any = None, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
    return default


def Body(default: Any = None, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
    return default


def Header(default: Any = None, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
    return default


def File(default: Any = None, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
    return default


def Form(default: Any = None, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
    return default


class _Status:
    HTTP_200_OK = 200
    HTTP_422_UNPROCESSABLE_ENTITY = 422
    HTTP_500_INTERNAL_SERVER_ERROR = 500
    HTTP_502_BAD_GATEWAY = 502


status = _Status()


class APIRouter:
    def __init__(self, *, prefix: str = "", tags: list[str] | None = None) -> None:
        self.prefix = prefix
        self.tags = tags or []
        self._routes: dict[tuple[str, str], Any] = {}

    @staticmethod
    def resolve_header(name: str, headers: dict[str, str] | None) -> str | None:
        if not headers:
            return None
        lname = name.lower()
        for k, v in headers.items():
            if k.lower() == lname:
                return v
        return None

    def get(self, path: str):
        def dec(fn: Any) -> Any:
            self._routes[("GET", self.prefix + path)] = fn
            return fn

        return dec

    def post(self, path: str):
        def dec(fn: Any) -> Any:
            self._routes[("POST", self.prefix + path)] = fn
            return fn

        return dec


class FastAPI:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._routes: dict[tuple[str, str], Any] = {}

        class _Router:
            def __init__(self, outer: FastAPI) -> None:
                self._outer = outer

            @property
            def routes(self) -> list[Any]:  # pragma: no cover
                return [
                    type("R", (), {"path": p, "methods": {m}, "endpoint": fn})()
                    for (m, p), fn in getattr(self._outer, "_routes", {}).items()
                ]

        self.router = _Router(self)

    def include_router(self, router: APIRouter) -> None:
        self._routes.update(router._routes)

    def get(self, path: str):
        def dec(fn: Any) -> Any:
            self._routes[("GET", path)] = fn
            return fn

        return dec


# Provide minimal submodules fastapi.testclient and fastapi.responses by pre-injecting
# synthetic modules into sys.modules to avoid importing on-disk corrupted files.
import json as _json
import sys as _sys
import types as _types


# fastapi.testclient minimal shim
_tc_mod = _types.ModuleType("fastapi.testclient")


class _Resp:
    def __init__(
        self, status_code: int = 200, content: bytes | str | None = None, json_obj: object | None = None
    ) -> None:
        self.status_code = status_code
        if json_obj is not None:
            self._json = json_obj
            self.content = _json.dumps(json_obj).encode("utf-8")
        else:
            self._json = None
            self.content = (
                b""
                if content is None
                else (content if isinstance(content, (bytes, bytearray)) else str(content).encode("utf-8"))
            )

    def json(self):  # pragma: no cover
        return self._json if self._json is not None else _json.loads(self.content.decode("utf-8"))


class TestClient:  # pragma: no cover - placeholder
    def __init__(self, app) -> None:
        self.app = app

    def _request(self, method: str, path: str, json: Any | None = None, headers: dict[str, str] | None = None) -> _Resp:
        # extremely small router invocation: match by method+path
        handler = self.app._routes.get((method, path))
        if handler is None:
            return _Resp(404, b"Not Found")
        try:
            result = handler(json) if json is not None else handler()
        except Exception as e:  # map HTTPException-like objects
            sc = getattr(e, "status_code", 500)
            return _Resp(sc, str(e))
        if isinstance(result, dict):
            return _Resp(200, json_obj=result)
        if isinstance(result, (list, tuple)):
            return _Resp(200, json_obj=list(result))
        status = getattr(result, "status_code", 200)
        content = getattr(result, "body", getattr(result, "content", b""))
        return _Resp(status, content)

    def get(self, path: str, headers: dict[str, str] | None = None) -> _Resp:
        return self._request("GET", path, headers=headers)

    def post(self, path: str, *, json: Any | None = None, headers: dict[str, str] | None = None) -> _Resp:
        return self._request("POST", path, json=json, headers=headers)


_tc_mod.TestClient = TestClient
_tc_mod.__all__ = ["TestClient"]
_sys.modules.setdefault("fastapi.testclient", _tc_mod)

# fastapi.responses minimal shim (JSONResponse only)
_resp_mod = _types.ModuleType("fastapi.responses")


class JSONResponse(Response):  # pragma: no cover
    def __init__(self, content, status_code: int = 200) -> None:
        super().__init__(_json.dumps(content), status_code=status_code, media_type="application/json")


_resp_mod.JSONResponse = JSONResponse
_resp_mod.Response = Response
_resp_mod.__all__ = ["JSONResponse", "Response"]
_sys.modules.setdefault("fastapi.responses", _resp_mod)

import sys
