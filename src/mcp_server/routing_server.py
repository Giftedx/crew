"""FastMCP Routing server (advisory) exposing cost and routing helpers.

Tools:
- estimate_cost(model, input_tokens, output_tokens)
- route_completion(task, tokens_hint=None)
- choose_embedding_model(dimensions_required=None)

Notes:
- Purely advisory. No LLM calls are made.
- Uses core.token_meter for pricing and token heuristics.
"""

from __future__ import annotations

try:
    from fastmcp import FastMCP  # type: ignore
except Exception as exc:  # pragma: no cover
    raise SystemExit("FastMCP is required for the routing MCP server. Install with 'pip install .[mcp]'.") from exc


routing_mcp = FastMCP("Routing Server")


def _load_pricing() -> dict[str, float]:
    try:
        from core import token_meter

        return dict(token_meter.MODEL_PRICES)
    except Exception:
        return {}


@routing_mcp.tool
def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> dict:
    """Estimate USD cost for a prospective call with given tokens and model.

    Returns: { usd: float, breakdown: { input_tokens, output_tokens, price_per_token } }
    """

    try:
        from core import token_meter

        price = float(_load_pricing().get(model, 0.0))
        usd = float(token_meter.estimate(int(input_tokens), int(output_tokens), model))
        return {
            "usd": usd,
            "breakdown": {
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
                "price_per_token": price,
            },
        }
    except Exception as exc:
        return {"usd": 0.0, "error": str(exc)}


@routing_mcp.tool
def route_completion(task: str, tokens_hint: dict | None = None) -> dict:
    """Suggest a model for a completion given a task description and optional token hints.

    Heuristic: pick lowest-cost available model when hints are small; otherwise prefer higher-quality
    model if available in pricing table. Returns advisory only: { model, reason, est_cost_usd, latency_class }.
    """

    try:
        from core import token_meter

        pricing = _load_pricing()
        if not pricing:
            return {"model": None, "reason": "no_pricing_available", "est_cost_usd": 0.0, "latency_class": "unknown"}

        # derive token estimates
        tokens_in = 0
        tokens_out = 0
        if isinstance(tokens_hint, dict):
            tokens_in = int(tokens_hint.get("input", 0) or 0)
            tokens_out = int(tokens_hint.get("output", 0) or 0)
        if tokens_in <= 0:
            tokens_in = int(token_meter.estimate_tokens(task))
        # very rough default output size
        if tokens_out <= 0:
            tokens_out = min(256, max(64, tokens_in // 2))

        # very simple heuristic: pick the cheapest model unless the task keyword suggests higher quality
        # sort models by price ascending
        by_price = sorted(pricing.items(), key=lambda kv: kv[1])
        preferred = by_price[0][0]
        reason = "lowest_cost"

        task_lower = (task or "").lower()
        if any(word in task_lower for word in ["analysis", "long", "summary", "evaluate", "reason"]):
            # choose the most expensive (proxy for higher quality) as a heuristic upper tier
            preferred = by_price[-1][0]
            reason = "higher_quality_heuristic"

        est = float(token_meter.estimate(tokens_in, tokens_out, preferred))
        latency_class = "low" if preferred == by_price[0][0] else ("high" if preferred == by_price[-1][0] else "medium")
        return {
            "model": preferred,
            "reason": reason,
            "est_cost_usd": est,
            "latency_class": latency_class,
            "tokens": {"input": tokens_in, "output": tokens_out},
        }
    except Exception as exc:
        return {"model": None, "reason": "error", "error": str(exc), "est_cost_usd": 0.0, "latency_class": "unknown"}


@routing_mcp.tool
def choose_embedding_model(dimensions_required: int | None = None) -> dict:
    """Return the embedding configuration used by this project.

    This project uses a deterministic 8-dim embedding helper for development and tests.
    Returns: { model: str, dimensions: int, note: str }
    """

    dims = 8  # from memory.embeddings (SHA-256 -> 8 floats)
    model_id = "internal:deterministic-8d"
    note = "Development/test embedding; production-grade models not configured here."
    if dimensions_required is not None and int(dimensions_required) != dims:
        note += f" Requested {int(dimensions_required)} dims; available {dims}."
    return {"model": model_id, "dimensions": dims, "note": note}


__all__ = ["routing_mcp", "estimate_cost", "route_completion", "choose_embedding_model"]
