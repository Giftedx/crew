from __future__ import annotations

# Minimal placeholder to satisfy rare imports in tests; not a full implementation.

class TestClient:  # pragma: no cover - placeholder
    def __init__(self, app) -> None:
        self.app = app
from __future__ import annotations

"""
Proxy submodule for fastapi.testclient that forwards to the real FastAPI package.
"""

        else:
            __all__ = []
                    query_items[k] = v if eq else ""
from pathlib import Path


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
except Exception:
    try:
        import fastapi_shim as _shim
  else:
      __all__ = []
                    query_items[k] = v if eq else ""
            req.query_params = query_items
        # Determine whether to pass request object based on handler signature
        sig = None
        with contextlib.suppress(TypeError, ValueError):  # builtins or C funcs
            sig = inspect.signature(handler)
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
                                    self._content = content

                                async def read(self):
                                    return self._content

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
            from pydantic import (
                BaseModel as _BM,
            )  # local import avoids hard dependency for non-pydantic tests

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
            return _Resp(
                200,
                json_obj={
                    "url": result.url,
                    "filename": result.filename,
                },
            )
        status = getattr(result, "status_code", 200)
        # Starlette Response uses `.body`; shim Response exposes `.content`
        content = getattr(result, "body", getattr(result, "content", b""))
        return _Resp(status, content)

    def post(
        self,
        path: str,
        *,
        json: Any | None = None,
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
        new_headers = {
            **(headers or {}),
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        return body, new_headers


def json_to_bytes(obj: Any) -> bytes:
    return json.dumps(obj).encode("utf-8")


# Backward compatibility alias - pytest won't collect this since it's not a class
TestClient = FastAPITestClient
