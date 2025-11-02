"""Pluggable reranker clients.

Provides a small, provider-agnostic interface for document reranking to boost
RAG results. The default implementation integrates with Cohere Rerank 3 using
the HTTP API via core.http_utils; additional providers can be added behind the
same interface without leaking vendor SDKs into the codebase.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from core.degradation_reporter import record_degradation
from platform.http.http_utils import REQUEST_TIMEOUT_SECONDS, resilient_post
from platform.config.configuration import get_config


@dataclass
class RerankResult:
    indexes: list[int]
    scores: list[float]


def _cohere_rerank(query: str, docs: list[str], top_n: int) -> RerankResult:
    cfg = get_config()
    api_key = getattr(cfg, "cohere_api_key", None)
    if not api_key:
        raise ValueError("COHERE_API_KEY not configured")
    payload = {
        "query": query,
        "documents": docs,
        "top_n": min(max(1, top_n), len(docs)),
        "model": "rerank-english-v3.0",
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = resilient_post(
        "https://api.cohere.ai/v1/rerank",
        json_payload=payload,
        headers=headers,
        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
    )
    data_any: Any
    try:
        data_any = resp.json()
    except Exception:
        data_any = {}
    data: dict[str, Any] = data_any if isinstance(data_any, dict) else {}
    results = data.get("results") if isinstance(data, dict) else None
    if not isinstance(results, list):
        record_degradation(
            component="rerank",
            event_type="cohere_identity_fallback",
            severity="warn",
            detail="cohere response missing results; using identity order",
        )
        return RerankResult(indexes=list(range(len(docs))), scores=[0.0] * len(docs))
    idxs: list[int] = []
    scores: list[float] = []
    for r in results:
        try:
            idxs.append(int(r.get("index")))
            scores.append(float(r.get("relevance_score", 0.0)))
        except Exception:
            continue
    if not idxs:
        idxs = list(range(len(docs)))
        scores = [0.0] * len(docs)
        record_degradation(
            component="rerank",
            event_type="cohere_empty_results",
            severity="warn",
            detail="cohere returned no usable indexes; identity order applied",
        )
    return RerankResult(indexes=idxs, scores=scores)


def rerank(query: str, docs: list[str], *, provider: str, top_n: int) -> RerankResult:
    prov = provider.lower().strip()
    if prov == "cohere":
        return _cohere_rerank(query, docs, top_n)
    if prov == "jina":
        cfg = get_config()
        api_key = getattr(cfg, "jina_api_key", None)
        if not api_key:
            raise ValueError("JINA_API_KEY not configured")
        payload = {
            "model": "jina-reranker-v2-base-en",
            "query": query,
            "documents": docs,
            "top_n": min(max(1, top_n), len(docs)),
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        resp = resilient_post(
            "https://api.jina.ai/v1/rerank",
            json_payload=payload,
            headers=headers,
            timeout_seconds=REQUEST_TIMEOUT_SECONDS,
        )
        try:
            data = resp.json()
        except Exception:
            data = {}
        results = data.get("results") if isinstance(data, dict) else None
        idxs: list[int] = []
        scores: list[float] = []
        if isinstance(results, list):
            for r in results:
                try:
                    idxs.append(int(r.get("index")))
                    scores.append(float(r.get("relevance_score", 0.0)))
                except Exception:
                    continue
        if not idxs:
            idxs = list(range(len(docs)))
            scores = [0.0] * len(docs)
            record_degradation(
                component="rerank",
                event_type="jina_empty_results",
                severity="warn",
                detail="jina returned no usable indexes; identity order applied",
            )
        return RerankResult(indexes=idxs, scores=scores)
    raise NotImplementedError(f"Rerank provider not implemented: {provider}")
