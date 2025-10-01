from __future__ import annotations

import json
import os
import re
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from uuid import uuid4

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool

try:  # pragma: no cover - optional heavy dependency
    import networkx as nx
except Exception:  # pragma: no cover
    nx = None  # type: ignore


def _normalise_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    normalised: dict[str, Any] = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            normalised[key] = value
        else:
            normalised[key] = repr(value)
    return normalised


def _split_sentences(text: str) -> list[str]:
    sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", text) if segment.strip()]
    if not sentences and text.strip():
        sentences = [text.strip()]
    return sentences


def _extract_keywords(text: str, *, limit: int = 12) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text)
    if not tokens:
        return []
    counts = Counter(token.lower() for token in tokens)
    return [token for token, _ in counts.most_common(limit)]


def _build_graph(text: str) -> dict[str, Any]:
    sentences = _split_sentences(text)
    keywords = _extract_keywords(text)
    if nx is None:
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            node_id = f"sentence_{idx + 1}"
            nodes.append({"id": node_id, "label": sentence})
            if idx > 0:
                edges.append(
                    {
                        "source": f"sentence_{idx}",
                        "target": node_id,
                        "relation": "sequence",
                    }
                )
        for kw in keywords:
            kw_id = f"keyword_{kw}"
            nodes.append({"id": kw_id, "label": kw, "type": "keyword"})
            if sentences:
                edges.append(
                    {
                        "source": kw_id,
                        "target": "sentence_1",
                        "relation": "mentions",
                    }
                )
        return {"nodes": nodes, "edges": edges, "keywords": keywords}

    graph = nx.DiGraph()
    for idx, sentence in enumerate(sentences):
        node_id = f"sentence_{idx + 1}"
        graph.add_node(node_id, label=sentence, type="sentence", order=idx + 1)
        if idx > 0:
            graph.add_edge(f"sentence_{idx}", node_id, relation="sequence")
    for kw in keywords:
        kw_id = f"keyword_{kw}"
        graph.add_node(kw_id, label=kw, type="keyword")
        for idx, sentence in enumerate(sentences[:3]):
            graph.add_edge(kw_id, f"sentence_{idx + 1}", relation="mentions")
    return {
        "nodes": [{"id": node, **(graph.nodes[node] or {})} for node in graph.nodes],
        "edges": [{"source": src, "target": dst, **(graph.edges[src, dst] or {})} for src, dst in graph.edges],
        "keywords": keywords,
    }


class GraphMemoryTool(BaseTool[StepResult]):
    """Persist lightweight knowledge graph structures for later retrieval.

    The tool accepts pre-filtered text (e.g. analysis summaries) and constructs
    a tenant-scoped graph capturing coarse relationships between sentences and
    extracted keywords. When Microsoft GraphRAG is available in the runtime it
    can be substituted by overriding the graph builder; the default
    implementation relies on ``networkx`` with a deterministic heuristic graph
    layout to remain lightweight and dependency-free during tests.
    """

    name: str = "Graph Memory Tool"
    description: str = "Store heuristic knowledge graphs derived from text in a tenant-scoped namespace."

    def __init__(self, storage_dir: str | os.PathLike[str] | None = None) -> None:
        super().__init__()
        base_dir = storage_dir or os.getenv("GRAPH_MEMORY_STORAGE", "crew_data/Processing/graph_memory")
        self._base_path = Path(base_dir)
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._metrics = get_metrics()

    @staticmethod
    def _physical_namespace(namespace: str) -> str:
        safe = namespace.replace(":", "__").replace("/", "_")
        return re.sub(r"[^A-Za-z0-9_.-]", "_", safe)

    def _namespace_path(self, namespace: str) -> Path:
        physical = self._physical_namespace(namespace)
        path = self._base_path / physical
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _resolve_namespace(self, index: str) -> tuple[str, bool]:
        try:
            from ultimate_discord_intelligence_bot.tenancy.context import current_tenant, mem_ns  # type: ignore

            ctx = current_tenant()
            if ctx is not None:
                return mem_ns(ctx, index), True
        except Exception:
            pass
        return index, False

    def run(
        self,
        *,
        text: str,
        index: str = "graph",
        metadata: dict[str, Any] | None = None,
        tags: Iterable[str] | None = None,
    ) -> StepResult:
        if not isinstance(text, str) or not text.strip():
            try:
                self._metrics.counter("tool_runs_total", labels={"tool": "graph_memory", "outcome": "skipped"}).inc()
            except Exception:
                pass
            return StepResult.skip(reason="empty_text")

        namespace, tenant_scoped = self._resolve_namespace(index)
        try:
            graph_payload = _build_graph(text)
            graph_id = uuid4().hex
            keywords = graph_payload.get("keywords") or []
            graph_payload["keywords"] = keywords
            graph_payload["metadata"] = {
                "tenant_scoped": tenant_scoped,
                "namespace": namespace,
                "keywords": keywords,
                "tags": list(tags or []),
                "source_metadata": _normalise_metadata(metadata),
            }
            graph_payload.setdefault("nodes", [])
            graph_payload.setdefault("edges", [])
            graph_payload["metadata"]["node_count"] = len(graph_payload["nodes"])
            graph_payload["metadata"]["edge_count"] = len(graph_payload["edges"])

            ns_path = self._namespace_path(namespace)
            file_path = ns_path / f"{graph_id}.json"
            with file_path.open("w", encoding="utf-8") as handle:
                json.dump(graph_payload, handle, ensure_ascii=False, indent=2)

            try:
                self._metrics.counter(
                    "tool_runs_total",
                    labels={"tool": "graph_memory", "outcome": "success", "tenant_scoped": str(tenant_scoped).lower()},
                ).inc()
            except Exception:
                pass

            return StepResult.ok(
                graph_id=graph_id,
                namespace=namespace,
                tenant_scoped=tenant_scoped,
                storage_path=str(file_path),
                node_count=len(graph_payload["nodes"]),
                edge_count=len(graph_payload["edges"]),
                keywords=graph_payload["metadata"].get("keywords", []),
            )
        except Exception as exc:  # pragma: no cover - defensive path
            try:
                self._metrics.counter(
                    "tool_runs_total",
                    labels={"tool": "graph_memory", "outcome": "error", "tenant_scoped": str(tenant_scoped).lower()},
                ).inc()
            except Exception:
                pass
            return StepResult.fail(str(exc), namespace=namespace)


__all__ = ["GraphMemoryTool"]
