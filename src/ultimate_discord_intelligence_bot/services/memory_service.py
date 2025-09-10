"""Simple in-memory retrieval service.

The :class:`MemoryService` provides a minimal interface for storing and
retrieving snippets of text.  It acts as a stand-in for a full vector database
so components can integrate memory lookups without requiring heavy
infrastructure during testing.
"""

from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from core.flags import enabled
from obs import metrics

from ..tenancy.context import TenantContext, current_tenant, mem_ns


@dataclass
class MemoryService:
    """Store and retrieve small text memories."""

    memories: list[dict[str, Any]] = field(default_factory=list)

    def add(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
        namespace: str | None = None,
    ) -> None:
        """Store a ``text`` snippet with optional ``metadata`` and ``namespace``.

            The snippet is passed through the privacy filter before storage so any
            personally identifiable information is redacted according to policy.
            Metadata values are kept as-is but may be coerced to strings during
            retrieval comparisons so non-string values such as integers are
        supported.
        """
        from ..privacy import privacy_filter  # noqa: PLC0415 - lazy import avoids circular during service wiring

        clean_text, _report = privacy_filter.filter_text(text, metadata or {})
        # Store copies so external mutations to ``metadata`` don't affect the
        # service's internal state.
        # Resolve tenant context with optional strict mode
        ctx = current_tenant()
        if ctx is None:
            if enabled("ENABLE_TENANCY_STRICT", False) or enabled("ENABLE_INGEST_STRICT", False):
                raise RuntimeError("TenantContext required but not set (strict mode)")
            logging.getLogger("tenancy").warning(
                "TenantContext missing; defaulting to 'default:main' namespace (non-strict mode)",
            )
            try:
                metrics.TENANCY_FALLBACKS.labels(**{**metrics.label_ctx(), "component": "memory_service"}).inc()
            except Exception as exc:
                # Metrics are optional; record debug without affecting control flow
                logging.debug("tenancy metric increment failed: %s", exc)
            ctx = TenantContext("default", "main")
        ns = namespace or mem_ns(ctx, "mem")
        self.memories.append({"namespace": ns, "text": clean_text, "metadata": deepcopy(metadata) or {}})

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        metadata: dict[str, Any] | None = None,
        namespace: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return stored memories matching ``query`` within ``namespace``.

        The search performs a case-insensitive substring match on the memory
        text. When ``metadata`` is supplied each key/value pair must also match
        the memory's metadata for it to be included in the results. Metadata
        comparisons are case-insensitive for both keys and values. Results are
        returned as deep copies and truncated to ``limit`` entries so callers
        cannot mutate the stored memories. ``limit`` values less than ``1`` or
        blank ``query`` strings short‑circuit the search and return an empty
        list.
        """

        query_norm = query.strip().lower()
        if limit < 1 or not query_norm:
            return []

        ctx = current_tenant()
        if ctx is None:
            if enabled("ENABLE_TENANCY_STRICT", False) or enabled("ENABLE_INGEST_STRICT", False):
                raise RuntimeError("TenantContext required but not set (strict mode)")
            logging.getLogger("tenancy").warning(
                "TenantContext missing; defaulting to 'default:main' namespace (non-strict mode)",
            )
            try:
                metrics.TENANCY_FALLBACKS.labels(**{**metrics.label_ctx(), "component": "memory_service"}).inc()
            except Exception as exc:
                logging.debug("tenancy metric increment failed: %s", exc)
            ctx = TenantContext("default", "main")
        ns = namespace or mem_ns(ctx, "mem")
        results = [m for m in self.memories if m.get("namespace") == ns and query_norm in m["text"].lower()]
        if metadata:
            lowered = {str(k).lower(): str(v).lower() for k, v in metadata.items()}
            filtered: list[dict[str, Any]] = []
            for m in results:
                meta_lower = {str(mk).lower(): str(mv).lower() for mk, mv in m["metadata"].items()}
                if all(meta_lower.get(k, "") == v for k, v in lowered.items()):
                    filtered.append(m)
            results = filtered
        # Return deep copies without the internal namespace key to protect
        # stored memories from caller mutation and avoid leaking prefixes.
        sanitized = []
        for m in results[:limit]:
            copy = deepcopy(m)
            copy.pop("namespace", None)
            sanitized.append(copy)
        return sanitized
