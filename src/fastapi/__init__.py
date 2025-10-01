from __future__ import annotations

import json
from collections.abc import Callable, Coroutine
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
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
    ) -> None:
        """Lightweight response object.

        Added media_type + body alias to satisfy tests that expect FastAPI/Starlette interface.
        """
        self.status_code = status_code
        self.content = content if isinstance(content, bytes) else str(content).encode("utf-8")
        self.headers: dict[str, str] = headers or {}
        self.media_type = media_type

    # Test suite expects a .body attribute; expose as property to avoid duplication
    @property
    def body(self) -> bytes:  # pragma: no cover - trivial alias
        return self.content


class Request:
    # Class-level placeholders so Mock(spec=Request) in tests exposes these attributes
    url = type("URL", (), {"path": "/", "query": "", "__str__": lambda self: getattr(self, "path", "/")})()
    headers: dict[str, str] = {}
    query_params: dict[str, str] = {}

    def __init__(
        self,
        body: bytes = b"",
        headers: dict[str, str] | None = None,
        method: str = "POST",
        path: str = "/",
        query: str = "",
    ) -> None:
        self._body = body
        self.headers = headers or {}
        self.method = method
        self.client = type("C", (), {"host": "localhost"})()
        # Provide simple url object with path + query attributes accessed by middleware/tests
        self.url = type("U", (), {"path": path, "query": query, "__str__": lambda self: path})()
        self.scope = {"route": type("R", (), {"path": path})()}
        # Parsed query parameters (populated by test client); remain empty by default
        self.query_params = {}

    async def body(self) -> bytes:
        return self._body

    async def json(self):  # pragma: no cover - trivial JSON parser used by endpoints
        import json as _json

        try:
            if isinstance(self._body, (bytes, bytearray)):
                return _json.loads(self._body.decode("utf-8"))
            # Allow tests to set body as pre-decoded string
            return _json.loads(str(self._body))
        except Exception as exc:
            raise ValueError(f"Invalid JSON: {exc}")


class APIRouter:
    def __init__(self, *, prefix: str = "", tags: list[str] | None = None) -> None:
        self.prefix = prefix
        self.tags = tags or []
        self._routes: dict[tuple[str, str], Callable[..., Any] | Coroutine[Any, Any, Any]] = {}

    def get(self, path: str):
        def dec(fn):
            self._routes[("GET", self.prefix + path)] = fn
            return fn

        return dec

    def post(self, path: str):
        def dec(fn):
            self._routes[("POST", self.prefix + path)] = fn
            return fn

        return dec

    # Minimal dependency-injection helpers for header alias matching
    @staticmethod
    def resolve_header(param_name: str, headers: dict[str, str]) -> str | None:
        """Resolve a header value for a given parameter name.

        Supports typical FastAPI style `X-API-TOKEN` -> `x_api_token` normalization.
        """
        target = param_name.replace("_", "-").upper()
        for k, v in headers.items():
            if k.upper() == target:
                return v
        return None


class FastAPI:
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # accept arbitrary args
        self._routes: dict[tuple[str, str], Callable[..., Any] | Coroutine[Any, Any, Any]] = {}
        self.service_name = kwargs.get("title", "app")

        # Expose a router-like shim with a .routes attribute for compatibility
        class _Router:
            def __init__(self, outer: FastAPI) -> None:
                self._outer = outer

            @property
            def routes(self) -> list[Any]:  # pragma: no cover - simple adapter
                items = []
                for (method, path), fn in getattr(self._outer, "_routes", {}).items():
                    items.append(type("R", (), {"path": path, "methods": {method}, "endpoint": fn})())
                return items

        self.router = _Router(self)

    def include_router(self, router: APIRouter) -> None:
        self._routes.update(router._routes)

    def get(self, path: str):
        def dec(fn):
            self._routes[("GET", path)] = fn
            return fn

        return dec

    def post(self, path: str):
        def dec(fn):
            self._routes[("POST", path)] = fn
            return fn

        return dec

    def middleware(self, _type: str):  # no-op for tests
        def dec(fn):
            return fn

        return dec


# Parameter helpers (dummies)
def file(default: Any) -> Any:  # pragma: no cover - placeholder
    return default


def form(default: Any) -> Any:  # pragma: no cover - placeholder
    return default


def header(default: Any, alias: str | None = None) -> Any:  # pragma: no cover - placeholder
    return default


def body(default: Any = ..., *, embed: bool | None = None) -> Any:  # pragma: no cover - placeholder
    """Mimic FastAPI's Body helper.

    Tests only validate that ``Body`` is importable and returns the provided
    sentinel/default value; argument handling is intentionally lightweight.
    """

    return default


# Preserve original FastAPI-esque names for compatibility
File = file
Form = form
Header = header
Body = body


class UploadFile:  # pragma: no cover - placeholder for typing only
    filename: str | None


# Submodule: responses
class _ResponsesModule:
    class JSONResponse(Response):  # pragma: no cover - minimal wrapper
        def __init__(self, content: Any, status_code: int = 200) -> None:
            super().__init__(json.dumps(content), status_code=status_code)


responses = _ResponsesModule()


# Minimal status constants used by the codebase/tests
class _StatusModule:
    HTTP_200_OK = 200
    HTTP_422_UNPROCESSABLE_ENTITY = 422
    HTTP_500_INTERNAL_SERVER_ERROR = 500
    HTTP_502_BAD_GATEWAY = 502


status = _StatusModule()
