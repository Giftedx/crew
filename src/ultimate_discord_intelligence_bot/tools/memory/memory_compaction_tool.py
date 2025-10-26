"""Compact tenant-scoped Qdrant memory by deleting expired points.

This tool evaluates expiration based on payload fields:
- created_at: unix epoch seconds when the point was created (int)
- _ttl: time-to-live in seconds (int)

If either field is missing, the point is considered non-expirable by this tool.
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING, Any, Protocol, TypedDict, runtime_checkable

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ...tenancy import current_tenant, mem_ns
from .._base import BaseTool


if TYPE_CHECKING:
    from collections.abc import Sequence


try:
    from memory.qdrant_provider import get_qdrant_client
except Exception:  # pragma: no cover - optional dependency in light envs

    def get_qdrant_client():  # type: ignore
        return None


@runtime_checkable
class _QdrantLike(Protocol):
    def get_collection(self, name: str) -> Any: ...
    def scroll(
        self,
        *,
        collection_name: str,
        limit: int = 100,
        with_payload: bool = True,
        offset: int | None = None,
        flt: Any | None = None,
    ) -> tuple[list[Any], int | None]: ...
    def delete_points(
        self,
        *,
        collection_name: str,
        ids: Sequence[int | str] | None = None,
        points: Sequence[int | str] | None = None,
        flt: Any | None = None,
    ) -> Any: ...


class _CompactionSummary(TypedDict, total=False):
    collection: str
    scanned: int
    deleted: int
    remaining: int
    tenant_scoped: bool


class MemoryCompactionTool(BaseTool[StepResult]):
    """Delete expired points from a tenant-scoped Qdrant collection."""

    name: str = "Qdrant Memory Compaction Tool"
    description: str = "Deletes expired memory points based on created_at + _ttl."

    from typing import ClassVar

    model_config: ClassVar[dict[str, Any]] = {"arbitrary_types_allowed": True, "extra": "allow"}

    def __init__(self, client: object | None = None, collection: str | None = None) -> None:
        super().__init__()
        self.base_collection = collection or os.getenv("QDRANT_COLLECTION", "content")
        self._metrics = get_metrics()
        if client is not None:
            self.client = client  # type: ignore[assignment]
        else:
            try:
                self.client = get_qdrant_client()
            except Exception:
                self.client = None

        # Flags
        self._enable_compaction = str(os.getenv("ENABLE_MEMORY_COMPACTION", "1")).lower() in {"1", "true", "yes", "on"}
        self._batch_size = int(os.getenv("MEMORY_COMPACTION_BATCH_SIZE", "200") or 200)

    @staticmethod
    def _physical_name(name: str) -> str:
        return name.replace(":", "__")

    def _get_collection(self, override: str | None) -> str:
        target_base = override or self.base_collection
        tenant_ctx = current_tenant()
        if tenant_ctx:
            return mem_ns(tenant_ctx, target_base)
        return target_base

    def _is_expired(self, payload: dict[str, Any], now: int) -> bool:
        try:
            created = int(payload.get("created_at", 0))
            ttl = int(payload.get("_ttl", 0))
        except Exception:
            return False
        if created <= 0 or ttl <= 0:
            return False
        return (created + ttl) <= now

    def _run(self, collection: str | None = None, max_delete: int | None = None) -> StepResult:
        if not self._enable_compaction:
            return StepResult.skip(reason="Compaction disabled via flag")
        if self.client is None:
            return StepResult.fail("Qdrant client not initialised")

        logical = self._get_collection(collection)
        physical = self._physical_name(logical)
        # Best-effort: ensure collection exists
        try:
            self.client.get_collection(physical)
        except Exception:
            # Nothing to compact
            return StepResult.ok(
                collection=logical,
                scanned=0,
                deleted=0,
                remaining=0,
                tenant_scoped=current_tenant() is not None,
            )

        scanned = 0
        deleted = 0
        now = int(time.time())
        offset: int | None = None
        ids_to_delete: list[Any] = []

        # Scroll through payloads to identify expirations
        while True:
            chunk, next_off = self.client.scroll(
                collection_name=physical,
                limit=self._batch_size,
                with_payload=True,
                offset=offset,
            )  # type: ignore[attr-defined]
            if not chunk:
                break
            for p in chunk:
                payload = getattr(p, "payload", {}) or {}
                pid = getattr(p, "id", None)
                scanned += 1
                if isinstance(payload, dict) and self._is_expired(payload, now) and pid is not None:
                    ids_to_delete.append(pid)
                    if max_delete is not None and len(ids_to_delete) >= max_delete:
                        break
            if max_delete is not None and len(ids_to_delete) >= max_delete:
                break
            offset = next_off
            if offset is None:
                break

        if ids_to_delete:
            # Delete in batches to avoid huge payloads
            for i in range(0, len(ids_to_delete), self._batch_size):
                batch = ids_to_delete[i : i + self._batch_size]
                self.client.delete_points(collection_name=physical, ids=batch)  # type: ignore[attr-defined]
            deleted = len(ids_to_delete)

        # Remaining is approximate for dummy client; best-effort compute
        try:
            # Re-scroll to count remaining
            remaining = 0
            offset = None
            while True:
                chunk, next_off = self.client.scroll(
                    collection_name=physical,
                    limit=self._batch_size,
                    with_payload=False,
                    offset=offset,
                )  # type: ignore[attr-defined]
                if not chunk:
                    break
                remaining += len(chunk)
                offset = next_off
                if offset is None:
                    break
        except Exception:
            remaining = -1

        self._metrics.counter(
            "tool_runs_total",
            labels={
                "tool": "memory_compaction",
                "outcome": "success",
                "tenant_scoped": str(current_tenant() is not None).lower(),
            },
        ).inc()
        return StepResult.ok(
            collection=logical,
            scanned=scanned,
            deleted=deleted,
            remaining=remaining,
            tenant_scoped=current_tenant() is not None,
        )

    def run(self, *args: Any, **kwargs: Any) -> StepResult:  # pragma: no cover - thin wrapper
        collection = kwargs.get("collection")
        max_delete = kwargs.get("max_delete")
        return self._run(collection=collection, max_delete=max_delete)


__all__ = ["MemoryCompactionTool"]
