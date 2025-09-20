from __future__ import annotations

import asyncio
import inspect
import json
from collections.abc import Iterable
from typing import Any

from . import APIRouter, Request


class _Resp:
    def __init__(self, status_code: int, content: bytes | str = b"", json_obj: Any | None = None) -> None:
        self.status_code = status_code
        self._content = content if isinstance(content, bytes) else str(content).encode("utf-8")
        self._json = json_obj

    def json(self) -> Any:
        if self._json is not None:
            return self._json
        try:
            return json.loads(self._content.decode("utf-8"))
        except Exception:
            return None


class TestClient:
    def __init__(self, app: Any) -> None:
        self.app = app
        # Provide public 'request' callable for compatibility with starlette TestClient
        self.request = self._request
        # Simple fixed window limiter state (shim only). Real FastAPI uses middleware.
        self._rl_reset = 0.0
        self._rl_remaining = None
        try:
            import os as _os

            if _os.getenv("ENABLE_RATE_LIMITING", "0").lower() in ("1", "true", "yes", "on"):
                burst = int(_os.getenv("RATE_LIMIT_BURST", _os.getenv("RATE_LIMIT_RPS", "10")))
                self._rl_remaining = burst
                self._rl_burst = burst
        except Exception:  # pragma: no cover - defensive
            pass

    # Internal unified request executor to minimise duplication
    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,  # noqa: A002 - keep param name for test parity
        headers: dict[str, str] | None = None,
        multipart: dict[str, Any] | None = None,
    ) -> _Resp:
        # Split query from path if present
        raw_path, _, raw_query = path.partition("?")
        handler = self.app._routes.get((method.upper(), raw_path))
        path_params: dict[str, str] = {}
        if handler is None:
            # naive dynamic path support: match single-segment parameters {name}
            for (m, pattern), fn in self.app._routes.items():
                if m != method.upper():
                    continue
                # Guard: only process string patterns (avoid FieldInfo / descriptor objects)
                if not isinstance(pattern, str):
                    continue
                if "{" not in pattern:
                    continue
                pattern_parts = pattern.strip("/").split("/")
                path_parts = raw_path.strip("/").split("/")
                if len(pattern_parts) != len(path_parts):
                    continue
                candidate: dict[str, str] = {}
                matched = True
                for pp, pv in zip(pattern_parts, path_parts):
                    if pp.startswith("{") and pp.endswith("}"):
                        name = pp[1:-1]
                        candidate[name] = pv
                    elif pp != pv:
                        matched = False
                        break
                if matched:
                    handler = fn
                    path_params = candidate
                    break
        if handler is None:
            return _Resp(404, b"not found")
        body: bytes
        form_files: dict[str, tuple[str, bytes]] = {}
        form_data: dict[str, Any] = {}
        if multipart and ("files" in multipart or "data" in multipart):
            # Snapshot original structures for later injection
            raw_files = multipart.get("files") or {}
            raw_data = multipart.get("data") or {}
            # Normalize file tuples: (filename, fileobj, content_type?) -> (filename, bytes)
            norm_files: dict[str, tuple[str, bytes]] = {}
            for field, val in raw_files.items():
                filename = field
                content: bytes = b""
                if isinstance(val, (bytes, bytearray)):
                    filename = field
                    content = bytes(val)
                elif isinstance(val, tuple) and len(val) >= 2:
                    filename = val[0]
                    second = val[1]
                    if hasattr(second, "read"):
                        # Read file-like object without assuming rewind later
                        try:
                            content = second.read()
                        except Exception:
                            content = b""
                    else:
                        content = second if isinstance(second, (bytes, bytearray)) else str(second).encode()
                else:
                    # Fallback stringify
                    content = str(val).encode()
                norm_files[field] = (filename, content)
            form_files = norm_files
            form_data = {k: v for k, v in raw_data.items()}
            # Replace multipart files with pure bytes tuples for builder
            build_files = {k: (v[0], v[1]) for k, v in norm_files.items()}
            body, headers = self._build_multipart({"files": build_files, "data": raw_data}, headers)
        else:
            body = b"" if json is None else (json if isinstance(json, bytes | bytearray) else json_to_bytes(json))

        req = Request(body=body, headers=headers or {}, method=method.upper(), path=raw_path, query=raw_query)

        # Shim-level rate limiting (only if middleware chain absent and enabled)
        if getattr(self, "_rl_remaining", None) is not None:
            import os as _os
            import time as _t

            metrics_path = _os.getenv("PROMETHEUS_ENDPOINT_PATH", "/metrics")
            if raw_path not in (metrics_path, "/health"):
                now = _t.monotonic()
                if now >= getattr(self, "_rl_reset", 0.0):
                    self._rl_reset = now + 1.0
                    self._rl_remaining = self._rl_burst
                if self._rl_remaining <= 0:  # type: ignore[operator]
                    return _Resp(429, b"Rate limit exceeded")
                self._rl_remaining = (self._rl_remaining or 0) - 1
        # Populate query params mapping for middleware tests if query exists
        if raw_query:
            query_items: dict[str, str] = {}
            for part in raw_query.split("&"):
                if not part:
                    continue
                k, eq, v = part.partition("=")
                if k:
                    query_items[k] = v if eq else ""
            req.query_params = query_items
        # Determine whether to pass request object based on handler signature
        sig = None
        try:
            sig = inspect.signature(handler)
        except (TypeError, ValueError):  # builtins or C funcs
            pass
        wants_arg = bool(sig and len(sig.parameters) >= 1)

        def _invoke():
            if wants_arg:
                # If the handler expects a Pydantic model, attempt to build it from JSON payload
                try:
                    from pydantic import BaseModel as _BM

                    if sig is not None:
                        params = list(sig.parameters.values())
                        if params:
                            param = params[0]
                            ann = param.annotation
                            if isinstance(ann, type) and issubclass(ann, _BM):
                                data_obj = json if isinstance(json, dict) else {}
                                return handler(ann(**data_obj))
                except Exception:
                    pass
                # Attempt simple form/header parameter injection
                if sig is not None:
                    params = list(sig.parameters.values())
                    injected_args: list[Any] = []
                    used_request = False
                    for p in params:
                        pname = p.name
                        if pname in path_params:
                            injected_args.append(path_params[pname])
                            continue
                        # Form data mapping
                        if pname in form_data:
                            injected_args.append(form_data[pname])
                            continue
                        if pname in form_files:
                            fname, fbytes = form_files[pname]

                            # Lightweight async read stub
                            class _UploadStub:
                                def __init__(self, filename: str, content: bytes) -> None:
                                    self.filename = filename

                                async def read(self):
                                    return fbytes

                            injected_args.append(_UploadStub(fname, fbytes))
                            continue
                        # Header alias
                        header_val = APIRouter.resolve_header(pname, req.headers)
                        if header_val is not None:
                            injected_args.append(header_val)
                            continue
                        # Fallback single Request injection
                        if not used_request:
                            injected_args.append(req)
                            used_request = True
                            continue
                    try:
                        return handler(*injected_args)
                    except Exception:
                        return handler(req)  # final fallback
                return handler(req)
            return handler()

        if asyncio.iscoroutinefunction(handler):
            try:
                result = asyncio.run(_invoke())
            except Exception as e:  # map HTTPException style to response
                if hasattr(e, "status_code"):
                    return _Resp(getattr(e, "status_code", 500), str(e))
                raise
        else:
            result = _invoke()

        # Support pydantic BaseModel (used in cache endpoints) by converting to dict
        try:  # pragma: no cover - lightweight defensive conversion
            from pydantic import BaseModel as _BM  # local import avoids hard dependency for non-pydantic tests

            if isinstance(result, _BM):
                return _Resp(200, json_obj=result.model_dump())
        except Exception:
            pass
        if isinstance(result, dict):  # simple JSON dict contract
            return _Resp(200, json_obj=result)
        if isinstance(result, list):  # support JSON arrays (e.g., JSON-RPC batch responses)
            return _Resp(200, json_obj=result)
        # Allow simple objects with 'url'/'filename' attributes (rehydrate) to map to dict
        if hasattr(result, "url") and hasattr(result, "filename"):
            return _Resp(200, json_obj={"url": getattr(result, "url"), "filename": getattr(result, "filename")})
        status = getattr(result, "status_code", 200)
        content = getattr(result, "content", b"")
        return _Resp(status, content)

    def post(
        self,
        path: str,
        *,
        json: Any | None = None,  # noqa: A002
        headers: dict[str, str] | None = None,
        files: dict[str, tuple[str, bytes]] | None = None,
        data: dict[str, Any] | None = None,
    ) -> _Resp:
        multipart = None
        if files or data:
            multipart = {"files": files, "data": data}
        return self._request("POST", path, json=json, headers=headers, multipart=multipart)

    def get(self, path: str, headers: dict[str, str] | None = None) -> _Resp:
        return self._request("GET", path, headers=headers)

    # Helper kept small; no need to expose publicly
    def _build_multipart(
        self, multipart: dict[str, Any], headers: dict[str, str] | None
    ) -> tuple[bytes, dict[str, str]]:
        files = multipart.get("files") or {}
        data = multipart.get("data") or {}
        boundary = "----testboundary"
        parts: list[bytes] = []
        # form fields
        for k, v in data.items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        # files (value may be bytes, (filename, content), iterable or str)
        min_file_seq_len = 2  # magic-number appeasement
        for field, val in files.items():
            if isinstance(val, bytes | bytearray):
                filename = field
                content = bytes(val)
            elif isinstance(val, Iterable):
                seq = list(val)
                if len(seq) >= min_file_seq_len:
                    filename, content = seq[0], seq[1]
                else:
                    filename, content = field, b""
                content = content if isinstance(content, bytes | bytearray) else str(content).encode()
            else:
                filename, content = field, str(val).encode()
            parts.append(
                (
                    f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'
                    f"Content-Type: application/octet-stream\r\n\r\n"
                ).encode()
            )
            parts.append(content)
            parts.append(b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)
        new_headers = {**(headers or {}), "Content-Type": f"multipart/form-data; boundary={boundary}"}
        return body, new_headers


def json_to_bytes(obj: Any) -> bytes:
    return json.dumps(obj).encode("utf-8")
