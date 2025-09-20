from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core import http_utils

Json = dict[str, Any]
JsonLike = Json | list[Json]


@dataclass
class A2AClientConfig:
    base_url: str
    api_key: str | None = None
    enable_retry: bool = False
    timeout_seconds: int = http_utils.REQUEST_TIMEOUT_SECONDS
    tenant_id: str | None = None
    workspace_id: str | None = None


class JsonRpcError(Exception):
    def __init__(self, code: int, message: str, data: Any | None = None):
        super().__init__(f"JSON-RPC error {code}: {message}")
        self.code = code
        self.data = data


class HttpError(Exception):
    def __init__(self, status_code: int, message: str | None = None):
        super().__init__(message or f"HTTP error: {status_code}")
        self.status_code = status_code


class A2AClient:
    def __init__(self, config: A2AClientConfig):
        self.config = config
        self._rpc_endpoint = self._join("/a2a/jsonrpc")
        self._agent_card = self._join("/a2a/agent-card")
        self._skills = self._join("/a2a/skills")

    def _join(self, path: str) -> str:
        base = self.config.base_url.rstrip("/")
        path = path if path.startswith("/") else f"/{path}"
        return f"{base}{path}"

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.config.api_key:
            h["X-API-Key"] = self.config.api_key
        if self.config.tenant_id:
            h["X-Tenant-Id"] = self.config.tenant_id
        if self.config.workspace_id:
            h["X-Workspace-Id"] = self.config.workspace_id
        return h

    @staticmethod
    def _ensure_ok(resp: Any) -> None:
        status = getattr(resp, "status_code", 200)
        if not (200 <= int(status) < 300):
            # Try to get meaningful text if available
            text = getattr(resp, "text", "")
            raise HttpError(int(status), text or None)

    # Discovery
    def get_agent_card(self) -> Json:
        if self.config.enable_retry:
            resp = http_utils.retrying_get(
                self._agent_card, headers=self._headers(), timeout_seconds=self.config.timeout_seconds
            )
        else:
            resp = http_utils.resilient_get(
                self._agent_card, headers=self._headers(), timeout_seconds=self.config.timeout_seconds
            )
        self._ensure_ok(resp)
        return resp.json()

    def get_skills(self) -> Json:
        if self.config.enable_retry:
            resp = http_utils.retrying_get(
                self._skills, headers=self._headers(), timeout_seconds=self.config.timeout_seconds
            )
        else:
            resp = http_utils.resilient_get(
                self._skills, headers=self._headers(), timeout_seconds=self.config.timeout_seconds
            )
        self._ensure_ok(resp)
        return resp.json()

    # RPC
    def call(self, method: str, params: Json | None = None, id_value: str | int = 1) -> Json:
        payload: Json = {"jsonrpc": "2.0", "id": id_value, "method": method}
        if params is not None:
            payload["params"] = params
        if self.config.enable_retry:
            resp = http_utils.retrying_post(
                self._rpc_endpoint,
                json_payload=payload,
                headers=self._headers(),
                timeout_seconds=self.config.timeout_seconds,
            )
        else:
            resp = http_utils.resilient_post(
                self._rpc_endpoint,
                json_payload=payload,
                headers=self._headers(),
                timeout_seconds=self.config.timeout_seconds,
            )
        self._ensure_ok(resp)
        data = resp.json()
        if isinstance(data, dict) and "error" in data:
            err = data["error"] or {}
            raise JsonRpcError(int(err.get("code", -32603)), str(err.get("message", "error")), err.get("data"))
        if not isinstance(data, dict) or "result" not in data:
            raise JsonRpcError(-32603, "Malformed JSON-RPC response", data)
        return data["result"]

    def call_batch(self, calls: list[tuple[str, Json | None, str | int]]) -> list[Json]:
        req: list[Json] = []
        for method, params, id_value in calls:
            item: Json = {"jsonrpc": "2.0", "id": id_value, "method": method}
            if params is not None:
                item["params"] = params
            req.append(item)
        if self.config.enable_retry:
            resp = http_utils.retrying_post(
                self._rpc_endpoint,
                json_payload=req,
                headers=self._headers(),
                timeout_seconds=self.config.timeout_seconds,
            )
        else:
            resp = http_utils.resilient_post(
                self._rpc_endpoint,
                json_payload=req,
                headers=self._headers(),
                timeout_seconds=self.config.timeout_seconds,
            )
        self._ensure_ok(resp)
        out = resp.json()
        if not isinstance(out, list):
            raise JsonRpcError(-32603, "Malformed batch response", out)
        results: list[Json] = []
        for item in out:
            if not isinstance(item, dict):
                raise JsonRpcError(-32603, "Malformed item in batch response", item)
            if "error" in item:
                err = item["error"] or {}
                raise JsonRpcError(int(err.get("code", -32603)), str(err.get("message", "error")), err.get("data"))
            if "result" not in item:
                raise JsonRpcError(-32603, "Missing result in batch response item", item)
            results.append(item["result"])
        return results
