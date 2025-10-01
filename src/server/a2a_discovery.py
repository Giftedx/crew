"""Discovery endpoints for the A2A adapter (agent-card and skills).

Separated from the main router for readability and maintainability.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from .a2a_schemas import (
    schema_lc_summarize,
    schema_rag_hybrid,
    schema_rag_ingest,
    schema_rag_ingest_url,
    schema_rag_query,
    schema_rag_query_vs,
    schema_research_and_brief,
    schema_research_and_brief_multi,
    schema_text_analyze,
)
from .a2a_tools import get_tools as _get_tools
from .a2a_tools import is_enabled as _is_enabled


def _skill_entries() -> list[dict[str, Any]]:
    tools_reg = _get_tools()
    skills: list[dict[str, Any]] = []

    if "tools.text_analyze" in tools_reg:
        skills.append(
            {
                "name": "tools.text_analyze",
                "description": "Analyze input text and return simple metrics (e.g., sentiment/keywords).",
                "input_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {"text": {"type": "string", "description": "Text to analyze"}},
                    "required": ["text"],
                    "additionalProperties": False,
                },
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {"type": "object"},
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.lc_summarize" in tools_reg:
        skills.append(
            {
                "name": "tools.lc_summarize",
                "description": "Extractive summarization: selects key sentences to form a concise summary.",
                "input_schema": schema_lc_summarize(),
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "summary": {"type": "string"},
                                "sentences": {"type": "array", "items": {"type": "string"}},
                                "count": {"type": "integer"},
                            },
                            "required": ["summary", "sentences"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.rag_query" in tools_reg:
        skills.append(
            {
                "name": "tools.rag_query",
                "description": "Rank a provided list of documents against a query using TF-IDF cosine.",
                "input_schema": schema_rag_query(),
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "hits": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "index": {"type": "integer"},
                                            "score": {"type": "number"},
                                            "snippet": {"type": "string"},
                                        },
                                        "required": ["index", "score", "snippet"],
                                    },
                                },
                                "count": {"type": "integer"},
                            },
                            "required": ["hits", "count"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.rag_query_vs" in tools_reg:
        skills.append(
            {
                "name": "tools.rag_query_vs",
                "description": "Query tenant-scoped vector index; optional offline fallback if documents provided.",
                "input_schema": schema_rag_query_vs(),
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "hits": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "text": {"type": "string"},
                                            "score": {"type": "number"},
                                            "payload": {"type": "object"},
                                        },
                                    },
                                },
                                "count": {"type": "integer"},
                                "source": {"type": "string", "enum": ["vector", "offline"]},
                            },
                            "required": ["hits", "count", "source"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.rag_ingest" in tools_reg:
        skills.append(
            {
                "name": "tools.rag_ingest",
                "description": "Chunk and upsert provided texts into a tenant-scoped vector index.",
                "input_schema": schema_rag_ingest(),
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "inserted": {"type": "integer"},
                                "chunks": {"type": "integer"},
                                "index": {"type": "string"},
                                "tenant_scoped": {"type": "boolean"},
                            },
                            "required": ["inserted", "chunks", "index", "tenant_scoped"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.rag_ingest_url" in tools_reg:
        skills.append(
            {
                "name": "tools.rag_ingest_url",
                "description": "Fetch HTTPS URLs, strip HTML, chunk and upsert into a tenant-scoped vector index.",
                "input_schema": schema_rag_ingest_url(),
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "fetched": {"type": "integer"},
                                "inserted": {"type": "integer"},
                                "chunks": {"type": "integer"},
                                "index": {"type": "string"},
                                "tenant_scoped": {"type": "boolean"},
                            },
                            "required": ["fetched", "inserted", "chunks", "index", "tenant_scoped"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.rag_hybrid" in tools_reg:
        skills.append(
            {
                "name": "tools.rag_hybrid",
                "description": "Hybrid retrieval combining vector search with offline TF-IDF and optional reranker.",
                "input_schema": schema_rag_hybrid(),
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "hits": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "text": {"type": "string"},
                                            "score": {"type": "number"},
                                            "source": {"type": "string"},
                                        },
                                    },
                                },
                                "count": {"type": "integer"},
                                "method": {"type": "string"},
                                "reranked": {"type": "boolean"},
                            },
                            "required": ["hits", "count", "method", "reranked"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.research_and_brief" in tools_reg:
        skills.append(
            {
                "name": "tools.research_and_brief",
                "description": "Synthesize outline and key findings from provided text sources (offline-safe).",
                "input_schema": schema_research_and_brief(),
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "outline": {"type": "array", "items": {"type": "string"}},
                                "key_findings": {"type": "array", "items": {"type": "string"}},
                                "citations": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {"type": {"type": "string"}, "index": {"type": "integer"}},
                                    },
                                },
                                "risks": {"type": "array", "items": {"type": "string"}},
                                "counts": {
                                    "type": "object",
                                    "properties": {
                                        "sources": {"type": "integer"},
                                        "tokens_estimate": {"type": "integer"},
                                    },
                                },
                            },
                            "required": ["outline", "key_findings", "citations", "risks", "counts"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    if "tools.research_and_brief_multi" in tools_reg:
        skills.append(
            {
                "name": "tools.research_and_brief_multi",
                "description": "Multi-agent augmented research and brief with offline fallback; strict time limits.",
                "input_schema": schema_research_and_brief_multi(),
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "outline": {"type": "array", "items": {"type": "string"}},
                                "key_findings": {"type": "array", "items": {"type": "string"}},
                                "citations": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {"type": {"type": "string"}, "index": {"type": "integer"}},
                                    },
                                },
                                "risks": {"type": "array", "items": {"type": "string"}},
                                "counts": {
                                    "type": "object",
                                    "properties": {
                                        "sources": {"type": "integer"},
                                        "tokens_estimate": {"type": "integer"},
                                    },
                                },
                                "meta": {
                                    "type": "object",
                                    "properties": {
                                        "multi_agent": {"type": "boolean"},
                                        "quality_score": {"type": ["number", "null"]},
                                        "execution_time": {"type": ["number", "null"]},
                                    },
                                },
                            },
                            "required": ["outline", "key_findings", "citations", "risks", "counts", "meta"],
                        },
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["status"],
                },
            }
        )

    return skills


def attach_discovery_routes(router: APIRouter) -> None:
    @router.get("/agent-card")
    async def agent_card():
        return {
            "id": "crew-discord-intelligence",
            "name": "Crew Discord Intelligence A2A Adapter",
            "version": "0.1.0",
            "protocol": "A2A-JSONRPC",
            "transport": "https",
            "endpoints": {"rpc": "/a2a/jsonrpc"},
            "skills": _skill_entries(),
            "auth": {"type": "none" if not _is_enabled("ENABLE_A2A_API_KEY", False) else "apiKey"},
            "description": "A minimal A2A-compatible adapter exposing selected tools over JSON-RPC.",
        }

    @router.get("/skills")
    async def list_skills():
        out = []
        for name in sorted(_get_tools().keys()):
            schema = None
            if name == "tools.text_analyze":
                schema = schema_text_analyze()
            elif name == "tools.lc_summarize":
                schema = schema_lc_summarize()
            elif name == "tools.rag_query":
                schema = schema_rag_query()
            elif name == "tools.rag_query_vs":
                schema = schema_rag_query_vs()
            elif name == "tools.rag_ingest":
                schema = schema_rag_ingest()
            elif name == "tools.rag_ingest_url":
                schema = schema_rag_ingest_url()
            elif name == "tools.rag_hybrid":
                schema = schema_rag_hybrid()
            elif name == "tools.research_and_brief":
                schema = schema_research_and_brief()
            elif name == "tools.research_and_brief_multi":
                schema = schema_research_and_brief_multi()
            out.append({"name": name, "input_schema": schema})
        return {"skills": out}


__all__ = ["attach_discovery_routes"]
