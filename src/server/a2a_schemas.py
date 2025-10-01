"""JSON Schema helpers for A2A skill discovery endpoints.

This keeps bulky schema literals out of the main router module.
"""

from __future__ import annotations

from typing import Any


def schema_text_analyze() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    }


def schema_lc_summarize() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "max_sentences": {"type": "integer", "minimum": 1, "maximum": 10, "default": 3},
        },
        "required": ["text"],
    }


def schema_rag_query() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "documents": {"type": "array", "items": {"type": "string"}},
            "top_k": {"type": "integer", "minimum": 1, "maximum": 25, "default": 3},
        },
        "required": ["query", "documents"],
    }


def schema_rag_query_vs() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "index": {"type": "string", "default": "memory"},
            "top_k": {"type": "integer", "minimum": 1, "maximum": 25, "default": 3},
            "documents": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["query"],
    }


def schema_rag_ingest() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "texts": {"type": "array", "items": {"type": "string"}},
            "index": {"type": "string", "default": "memory"},
            "chunk_size": {"type": "integer", "minimum": 50, "maximum": 2000, "default": 400},
            "overlap": {"type": "integer", "minimum": 0, "maximum": 500, "default": 50},
        },
        "required": ["texts"],
    }


def schema_rag_ingest_url() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "urls": {"type": "array", "items": {"type": "string"}},
            "index": {"type": "string", "default": "memory"},
            "chunk_size": {"type": "integer", "minimum": 50, "maximum": 2000, "default": 400},
            "overlap": {"type": "integer", "minimum": 0, "maximum": 500, "default": 50},
            "max_bytes": {"type": "integer", "minimum": 1000, "maximum": 2000000, "default": 500000},
        },
        "required": ["urls"],
    }


def schema_rag_hybrid() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "index": {"type": "string", "default": "memory"},
            "candidate_docs": {"type": "array", "items": {"type": "string"}},
            "top_k": {"type": "integer", "minimum": 1, "maximum": 25, "default": 5},
            "alpha": {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.7},
            "enable_rerank": {"type": ["boolean", "null"], "default": None},
        },
        "required": ["query"],
    }


def schema_research_and_brief() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "sources_text": {"type": ["array", "null"], "items": {"type": "string"}},
            "max_items": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
        },
        "required": ["query"],
    }


def schema_research_and_brief_multi() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "sources_text": {"type": ["array", "null"], "items": {"type": "string"}},
            "max_items": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
            "max_time": {"type": "number", "minimum": 5.0, "maximum": 300.0, "default": 60.0},
            "enable_alerts": {"type": "boolean", "default": False},
        },
        "required": ["query"],
    }


__all__ = [
    "schema_text_analyze",
    "schema_lc_summarize",
    "schema_rag_query",
    "schema_rag_query_vs",
    "schema_rag_ingest",
    "schema_rag_ingest_url",
    "schema_rag_hybrid",
    "schema_research_and_brief",
    "schema_research_and_brief_multi",
]
